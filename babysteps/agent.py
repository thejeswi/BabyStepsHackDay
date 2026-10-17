"""The agent loop: one conversation, Claude + browser tools, events streamed to the chat UI.

History is append-only (required for thinking blocks on current models): every response's
full content is appended unchanged, followed by the tool results.
"""
import json
import time
from typing import Any, Awaitable, Callable

import anthropic

from . import config, memory, vault
from .browser import Browser, ToolError
from .prompt import SYSTEM_PROMPT

Emit = Callable[[dict], Awaitable[None]]


def _tool(name: str, description: str, props: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": False,
        },
    }


REF = {"type": "integer", "description": "Element number from the latest read_page."}

TOOLS = [
    _tool("read_page", "Read the current page: URL, numbered interactive elements, visible text.", {}, []),
    _tool("open_url", "Open a web address in the browser.", {"url": {"type": "string"}}, ["url"]),
    _tool(
        "click",
        "Click an element. Buttons that send, buy, pay, delete or confirm are refused until the "
        "user has answered your question; after the user said yes, call again with confirmed=true.",
        {"ref": REF, "confirmed": {"type": "boolean", "description": "true only after the user agreed in the chat."}},
        ["ref", "confirmed"],
    ),
    _tool(
        "type_text",
        "Type text into a text box (replaces what is there). Refused for password and code fields.",
        {"ref": REF, "text": {"type": "string"}, "press_enter": {"type": "boolean"}},
        ["ref", "text", "press_enter"],
    ),
    _tool("select_option", "Choose an option in a drop-down list.", {"ref": REF, "option": {"type": "string"}}, ["ref", "option"]),
    _tool(
        "ask_user_to_type",
        "Mark a box on the user's screen with an orange frame so THEY can type a secret "
        "(password, code, PIN). Then tell them in the chat what to type there and to say when done.",
        {"ref": REF},
        ["ref"],
    ),
    _tool("scroll", "Scroll the page.", {"direction": {"type": "string", "enum": ["up", "down"]}}, ["direction"]),
    _tool("go_back", "Go back to the previous page.", {}, []),
    _tool(
        "list_passwords",
        "List the user's password book: entry names, sites and usernames. Passwords are never shown to you.",
        {}, [],
    ),
    _tool(
        "fill_password",
        "Fill a saved password into password box(es) on the current page, by entry name. Only works "
        "on the site the entry belongs to. You never see the password.",
        {"entry": {"type": "string"}, "refs": {"type": "array", "items": {"type": "integer"}}},
        ["entry", "refs"],
    ),
    _tool(
        "new_password",
        "Make a new strong random password, save it in the password book under the current page's "
        "site, and fill it into the given box(es) (e.g. 'password' and 'repeat password').",
        {"entry": {"type": "string", "description": "Name for the entry, e.g. 'Example Mail (inge.mueller@example.mail)'."},
         "username": {"type": "string"},
         "refs": {"type": "array", "items": {"type": "integer"}}},
        ["entry", "username", "refs"],
    ),
    _tool(
        "save_typed_password",
        "Save the password the USER typed into a box into the password book (you don't see it).",
        {"entry": {"type": "string"}, "username": {"type": "string"}, "ref": REF},
        ["entry", "username", "ref"],
    ),
    # Anthropic-defined memory tool: schema-less, backed by babysteps/memory.py.
    {"type": "memory_20250818", "name": "memory"},
]


class Agent:
    def __init__(self, browser: Browser) -> None:
        self.browser = browser
        self.client = anthropic.AsyncAnthropic()
        self.messages: list[dict[str, Any]] = []
        # Irreversible clicks: blocked until a user message arrives after the block.
        self._pending_confirmation: int | None = None
        self._user_spoke_since_block = False
        self._log_path = config.LOG_DIR / f"session-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"

    def reset(self) -> None:
        self.messages = []
        self._pending_confirmation = None
        self._user_spoke_since_block = False

    def _log(self, kind: str, payload: Any) -> None:
        with self._log_path.open("a") as f:
            f.write(json.dumps({"t": time.time(), "kind": kind, "data": payload}, default=str) + "\n")

    async def _call_model(self):
        kwargs = dict(
            model=config.MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=self.messages,
            thinking={"type": "adaptive"},
            output_config={"effort": config.EFFORT},
        )
        if config.USE_FALLBACKS:
            return await self.client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
            )
        return await self.client.messages.create(**kwargs)

    async def _run_tool(self, name: str, args: dict, emit: Emit) -> str:
        b = self.browser
        if name == "read_page":
            await emit({"type": "action", "text": "Looking at the page"})
            return await b.read_page()
        if name == "open_url":
            await emit({"type": "action", "text": f"Opening {args['url']}"})
            return await b.open_url(args["url"])
        if name == "click":
            ref = args["ref"]
            label = await b.element_text(ref)
            if b.looks_irreversible(label):
                ok = args["confirmed"] and self._pending_confirmation == ref and self._user_spoke_since_block
                if not ok:
                    self._pending_confirmation = ref
                    self._user_spoke_since_block = False
                    await emit({"type": "action", "text": f"Waiting for your OK before clicking “{label}”"})
                    return (
                        f"NOT clicked: “{label}” can't be undone. Ask the user in plain words whether "
                        "to go ahead, then stop and wait for their answer. If they say yes, call click "
                        "again with confirmed=true."
                    )
                self._pending_confirmation = None
            await emit({"type": "action", "text": f"Clicking “{label or ref}”"})
            return await b.click(ref)
        if name == "type_text":
            await emit({"type": "action", "text": f"Typing “{args['text']}”"})
            return await b.type_text(args["ref"], args["text"], args["press_enter"])
        if name == "select_option":
            await emit({"type": "action", "text": f"Choosing “{args['option']}”"})
            return await b.select_option(args["ref"], args["option"])
        if name == "ask_user_to_type":
            await emit({"type": "action", "text": "Marking the box for you (orange frame)"})
            return await b.highlight(args["ref"])
        if name == "scroll":
            await emit({"type": "action", "text": f"Scrolling {args['direction']}"})
            return await b.scroll(args["direction"])
        if name == "list_passwords":
            await emit({"type": "action", "text": "Looking in your password book"})
            return vault.listing()
        if name == "fill_password":
            entry = vault.get(args["entry"])
            vault.check_site(entry, b.url())
            if not args["refs"]:
                raise ToolError("Give at least one box number")
            for ref in args["refs"]:
                await b.fill_secret(ref, entry["password"])
            await emit({"type": "action", "text": f"Filling in your saved password for “{args['entry']}”"})
            return f"Filled the saved password into {args['refs']}. (You don't see it.)"
        if name == "new_password":
            if not args["refs"]:
                raise ToolError("Give the box number(s) to fill")
            pw = vault.generate()
            for ref in args["refs"]:
                await b.fill_secret(ref, pw)
            vault.put(args["entry"], vault.site_of(b.url()), args["username"], pw)
            await emit({"type": "action", "text": f"Made a new password and saved it in your password book as “{args['entry']}”"})
            return (f"New password filled into {args['refs']} and saved as {args['entry']!r} for "
                    f"{vault.site_of(b.url())}. Note: if the form is not submitted successfully, the saved "
                    "password may not match the account.")
        if name == "save_typed_password":
            pw = await b.read_secret(args["ref"])
            vault.put(args["entry"], vault.site_of(b.url()), args["username"], pw)
            await emit({"type": "action", "text": f"Saved your password in your password book as “{args['entry']}”"})
            return f"Saved what the user typed in [{args['ref']}] as {args['entry']!r}."
        if name == "memory":
            if args["command"] != "view":
                await emit({"type": "action", "text": "Making a note for next time"})
            return memory.handle(args)
        if name == "go_back":
            await emit({"type": "action", "text": "Going back"})
            return await b.go_back()
        raise ToolError(f"Unknown tool {name}")

    async def handle_user_message(self, text: str, emit: Emit) -> None:
        self._user_spoke_since_block = True
        self.messages.append({"role": "user", "content": text})
        self._log("user", text)

        for _ in range(config.MAX_STEPS_PER_TURN):
            response = await self._call_model()
            self._log("response", response.model_dump())
            self.messages.append({"role": "assistant", "content": response.content})

            for block in response.content:
                if block.type == "text" and block.text.strip():
                    await emit({"type": "assistant", "text": block.text})

            if response.stop_reason == "refusal":
                await emit({"type": "assistant", "text": "Sorry, I can't help with that one."})
                return
            if response.stop_reason == "max_tokens":
                raise RuntimeError("Model hit max_tokens; answer cut off")
            if response.stop_reason != "tool_use":
                return  # end_turn: waiting for the user

            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    out = await self._run_tool(block.name, block.input, emit)
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
                except ToolError as e:
                    await emit({"type": "action", "text": f"Problem: {e}"})
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(e), "is_error": True})
            self._log("tool_results", results)
            self.messages.append({"role": "user", "content": results})

        await emit({"type": "assistant", "text": "This is taking me too many steps. Shall I keep going?"})
