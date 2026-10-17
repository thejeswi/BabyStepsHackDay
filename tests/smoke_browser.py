"""Smoke test of the browser tools and safety blocks, without the Claude API.

Run: BABYSTEPS_HEADLESS=1 .venv/bin/python tests/smoke_browser.py
"""
import asyncio
import threading
import time

import uvicorn

from babysteps import config
from babysteps.browser import Browser, ToolError
from fastapi import FastAPI
from babysteps import mock_site

app = FastAPI()
app.include_router(mock_site.router)


def serve():
    uvicorn.run(app, host="127.0.0.1", port=config.PORT, log_level="warning")


async def main():
    threading.Thread(target=serve, daemon=True).start()
    time.sleep(1.5)
    b = Browser()
    await b.start()
    print(await b.open_url(f"{config.BASE_URL}/mock/"))
    page = await b.read_page()
    print(page[:900])
    # find refs
    refs = {line.split("]")[0][1:]: line for line in page.splitlines() if line.startswith("[")}
    email = next(r for r, l in refs.items() if "type=email" in l)
    pw = next(r for r, l in refs.items() if "type=password" in l)
    print(await b.type_text(int(email), "ayse.yilmaz@example.mail", False))
    try:
        await b.type_text(int(pw), "secret", False)
        raise SystemExit("FAIL: password typing was allowed")
    except ToolError as e:
        print("OK password blocked:", e)
    print(await b.highlight(int(pw)))
    from babysteps.browser import path_blocked, scheme_allowed
    assert scheme_allowed("https://any-site.example/x") and not path_blocked("https://any-site.example/passwords")
    print("OK any website allowed (no allowlist)")
    for bad in ["file:///etc/hosts", f"{config.BASE_URL}/mock/phone", f"{config.BASE_URL}/passwords"]:
        try:
            await b.open_url(bad)
            raise SystemExit(f"FAIL: {bad} opened")
        except ToolError as e:
            print("OK blocked:", bad)
    print("irreversible('Send')", b.looks_irreversible("Send"), "| ('Log in')", b.looks_irreversible("Log in"),
          "| ('Delete account')", b.looks_irreversible("Delete account"), "| ('Code per SMS anfordern')", b.looks_irreversible("Code per SMS anfordern"))
    # forgot-password flow: code field must count as secret
    await b.open_url(f"{config.BASE_URL}/mock/forgot")
    p = await b.read_page(); r = next(l for l in p.splitlines() if "type=email" in l).split("]")[0][1:]
    print(await b.type_text(int(r), "ayse.yilmaz@example.mail", True))
    p = await b.read_page(); print(p[:700])
    code = next(l for l in p.splitlines() if 'name="code"' in l).split("]")[0][1:]
    try:
        await b.type_text(int(code), "123456", False); raise SystemExit("FAIL: code typing allowed")
    except ToolError:
        print("OK code field blocked")
    # scam link to an external .exe: allowed to navigate (no allowlist); must not crash or download
    from babysteps.mock_site import ACCOUNTS
    ACCOUNTS["ayse.yilmaz@example.mail"]["password"] = "testtest1"
    await b.open_url(f"{config.BASE_URL}/mock/")
    await b._page().fill("#email", "ayse.yilmaz@example.mail"); await b._page().fill("#password", "testtest1")
    await b._page().click("button"); await b._settle()
    p = await b.read_page()
    link = next(l for l in p.splitlines() if "SecurityTool" in l).split("]")[0][1:]
    print(await b.click(int(link)))
    print("now on:", b._page().url)
    await b.stop()
    print("ALL SMOKE CHECKS PASSED")

asyncio.run(main())
