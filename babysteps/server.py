"""Web server: chat UI at /, chat websocket at /ws, practice site at /mock.

Run with: python -m babysteps
"""
import asyncio
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config, mock_site
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
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(config.STATIC_DIR / "index.html")


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
            if msg["type"] != "user":
                raise ValueError(f"Unknown message type {msg['type']!r}")
            async with state["lock"]:
                await emit({"type": "busy"})
                try:
                    await agent.handle_user_message(msg["text"], emit)
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
