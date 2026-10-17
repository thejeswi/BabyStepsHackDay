"""Web server: chat UI at /, chat websocket at /ws, practice site at /mock.

Run with: python -m babysteps
"""
import asyncio
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import html

from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import city_site, config, memory, mock_site, vault
from .documents import DOCUMENTS, compose_message
from .agent import Agent
from .browser import Browser

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    browser = Browser()
    state["browser"] = browser
    # Start the browser after the server is listening: its first page is served by us.
    def _start_browser() -> None:
        task = asyncio.ensure_future(browser.start())
        # Surface browser start-up failures loudly instead of losing them in a background task.
        task.add_done_callback(lambda t: t.exception() and traceback.print_exception(t.exception()))

    asyncio.get_running_loop().call_later(1.0, _start_browser)
    state["agent"] = Agent(browser)
    state["lock"] = asyncio.Lock()
    yield
    await browser.stop()


app = FastAPI(lifespan=lifespan)
app.include_router(mock_site.router)
app.include_router(city_site.router)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(config.STATIC_DIR / "index.html")


@app.get("/api/documents")
def documents() -> dict:
    return {k: {"button": d["button"], "title": d["title"], "text": d["text"]} for k, d in DOCUMENTS.items()}


@app.get("/memory")
def memory_page() -> HTMLResponse:
    """What the helper remembers, for the family to read (and check)."""
    files = memory.dump()
    body = "".join(f"<h2>{html.escape(n)}</h2><pre>{html.escape(t)}</pre>" for n, t in files) or "<p>Nothing yet.</p>"
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><title>What BabySteps remembers</title>"
        "<style>body{font-family:Helvetica,Arial,sans-serif;font-size:20px;max-width:760px;margin:30px auto;"
        "background:#fdf8f0}pre{white-space:pre-wrap;background:#fff;padding:16px;border-radius:10px}</style>"
        f"<h1>What BabySteps remembers</h1><p>Files in <code>{html.escape(str(config.MEMORY_DIR))}</code>. "
        f"You can edit or delete them.</p>{body}"
    )


@app.get("/passwords")
def passwords_page() -> HTMLResponse:
    """The password book, for the human only (the agent's browser is blocked from this path)."""
    rows = "".join(
        f"<tr><td>{html.escape(e['name'])}</td><td>{html.escape(e['site'])}</td><td>{html.escape(e['username'])}</td>"
        f"<td><details><summary>show</summary><code>{html.escape(e['password'])}</code></details></td></tr>"
        for e in vault.entries_for_human()
    ) or "<tr><td colspan=4>Empty so far.</td></tr>"
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><title>Password book</title>"
        "<style>body{font-family:Helvetica,Arial,sans-serif;font-size:20px;max-width:900px;margin:30px auto;"
        "background:#fdf8f0}table{border-collapse:collapse;width:100%;background:#fff}td,th{padding:10px;"
        "border-bottom:1px solid #ddd;text-align:left}code{font-size:22px}</style>"
        "<h1>🔑 Your password book</h1><p>BabySteps fills these in for you. It cannot see them.</p>"
        f"<table><tr><th>Name</th><th>Website</th><th>Username</th><th>Password</th></tr>{rows}</table>"
    )


@app.websocket("/ws")
async def ws(socket: WebSocket) -> None:
    await socket.accept()
    agent: Agent = state["agent"]

    async def emit(event: dict) -> None:
        await socket.send_json(event)

    try:
        while True:
            msg = await socket.receive_json()
            if msg["type"] == "reset":
                agent.reset()
                await emit({"type": "reset"})
                continue
            if msg["type"] == "document":
                text = compose_message(msg["id"], msg["text"])
            elif msg["type"] == "user":
                text = msg["text"]
            else:
                raise ValueError(f"Unknown message type {msg['type']!r}")
            async with state["lock"]:
                await emit({"type": "busy"})
                try:
                    await agent.handle_user_message(text, emit)
                except Exception as e:
                    traceback.print_exc()
                    await emit({"type": "error", "text": f"{type(e).__name__}: {e}"})
                await emit({"type": "done"})
    except WebSocketDisconnect:
        pass


def main() -> None:
    config.require_api_key()
    print(f"\n  Chat:  {config.BASE_URL}/\n  Phone: {config.BASE_URL}/mock/phone  (fake phone for the human)\n")
    uvicorn.run(app, host="127.0.0.1", port=config.PORT, log_level="warning")
