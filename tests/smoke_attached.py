"""Smoke test of attached mode (BABYSTEPS_CDP_URL): Playwright joins a running Chrome.

Starts the repo's Chrome headless on a throwaway profile, then checks what differs from
launched mode: only the agent's tabs are limited, tabs it opens are limited too, downloads
are denied, and a closed agent tab is replaced. No API key needed.
Run: BABYSTEPS_PORT=8015 .venv/bin/python tests/smoke_attached.py
"""
import asyncio
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

CDP_PORT = 9445
DOWNLOAD_NAME = f"bs-smoke-{os.getpid()}.bin"
os.environ["BABYSTEPS_CDP_URL"] = f"http://127.0.0.1:{CDP_PORT}"

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

from babysteps import config, mock_site
from babysteps.browser import Browser, ToolError

app = FastAPI()
app.include_router(mock_site.router)


@app.get("/passwords")
def passwords() -> HTMLResponse:
    return HTMLResponse("<h1>password book</h1>")


@app.get("/file.bin")
def file_bin() -> Response:
    return Response(b"x" * 100, media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment; filename={DOWNLOAD_NAME}"})


@app.get("/opener")
def opener() -> HTMLResponse:
    return HTMLResponse('<a id=out target=_blank href="/mock/phone">out</a>'
                        '<a id=dl href="/file.bin">download</a>')


def chrome_binary() -> str:
    if platform.system() == "Darwin":
        return str(config.ROOT / "chrome/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
    return str(config.ROOT / "chrome/chrome")


async def main() -> None:
    profile = tempfile.mkdtemp(prefix="bs-attached-")
    chrome = subprocess.Popen(
        [chrome_binary(), "--headless=new", "--no-sandbox", f"--user-data-dir={profile}",
         f"--remote-debugging-port={CDP_PORT}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version")
                break
            except OSError:
                time.sleep(0.5)
        threading.Thread(
            target=lambda: uvicorn.run(app, host="127.0.0.1", port=config.PORT, log_level="warning"),
            daemon=True,
        ).start()
        time.sleep(1.5)

        b = Browser()
        await b.start()
        assert len(b._context.pages) == 1, f"start tab not reused: {[p.url for p in b._context.pages]}"
        print("OK reused Chrome's start tab:", b.url())

        # The user's own tab: no allowlist, and the human-only password book opens.
        user_tab = await b._context.new_page()
        await user_tab.goto(f"{config.BASE_URL}/passwords")
        assert "password book" in await user_tab.content()
        print("OK user's tab may open /passwords")
        assert b.page is not user_tab, "agent must not follow tabs the user opens"

        # The agent still can't.
        try:
            await b.open_url(f"{config.BASE_URL}/passwords")
            raise SystemExit("FAIL: agent opened /passwords")
        except ToolError:
            print("OK agent blocked from /passwords")

        # A tab the agent opens (target=_blank) is followed and limited.
        await b.open_url(f"{config.BASE_URL}/opener")
        agent_tab = b.page
        await b._page().click("#out")
        await asyncio.sleep(1.5)
        assert b.page is not agent_tab, "agent did not follow its new tab"
        assert "/mock/phone" not in b.url(), f"new tab reached the human-only phone page: {b.url()}"
        print("OK agent's new tab followed; human-only page blocked:", b.url(), b.blocked_log)
        await b.page.close()
        assert b.page is agent_tab, "agent did not fall back to its previous tab"
        print("OK fell back to previous tab after close")

        # Downloads are denied browser-wide.
        events = []
        b._page().on("download", lambda d: events.append(d))
        await b._page().click("#dl")
        await asyncio.sleep(1.5)
        assert events, "test page did not start a download"
        failures = [await d.failure() for d in events]
        assert failures == ["canceled"], f"download not canceled: {failures}"
        assert not (Path.home() / "Downloads" / DOWNLOAD_NAME).exists(), "download happened"
        print("OK download denied")

        # Closing the agent's last tab: tools say so, open_url opens a new one.
        await agent_tab.close()
        try:
            await b.read_page()
            raise SystemExit("FAIL: read_page worked without a tab")
        except ToolError as e:
            print("OK closed tab reported:", e)
        print(await b.open_url(f"{config.BASE_URL}/mock/"))

        await b.stop()
        assert chrome.poll() is None, "stop() must not close the user's Chrome"
        print("OK Chrome still running after stop()")
        print("ALL ATTACHED CHECKS PASSED")
    finally:
        chrome.terminate()
        chrome.wait()
        shutil.rmtree(profile, ignore_errors=True)


asyncio.run(main())
