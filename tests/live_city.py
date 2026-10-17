"""Live run of the letter / city-portal demo scenes (uses the API, about $1-2).

Run: BABYSTEPS_HEADLESS=1 BABYSTEPS_PORT=8018 .venv/bin/python tests/live_city.py
"""
import asyncio
import os
import tempfile
import threading
import time

os.environ.setdefault("BABYSTEPS_MEMORY_DIR", tempfile.mkdtemp(prefix="bs-mem-"))
os.environ.setdefault("BABYSTEPS_VAULT_FILE", tempfile.mkdtemp(prefix="bs-vault-") + "/vault.json")

import uvicorn
from fastapi import FastAPI

from babysteps import city_site, config, mock_site
from babysteps.agent import Agent
from babysteps.browser import Browser
from babysteps.documents import compose_message

app = FastAPI()
app.include_router(mock_site.router)
app.include_router(city_site.router)


async def emit(ev):
    print(f"  <{ev['type']}> {ev.get('text', '')}")


async def say(agent, text, label=None):
    print(f"\nUSER: {label or text}")
    await agent.handle_user_message(text, emit)


async def main():
    threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=config.PORT, log_level="warning"), daemon=True).start()
    time.sleep(1.5)
    b = Browser(); await b.start(); a = Agent(b)

    print("=== Scene 1: Bürgeramt appointment -> online application")
    await say(a, "I have to go to the Bürgeramt for my citizenship. Can you make an appointment for me?")
    await say(a, "Yes please. My name is Ayşe Yılmaz, born 03.05.1962, Turkish, in Germany since 1998. I have B1 and I passed the test.")
    await say(a, "Yes, send it.")
    print("SUBMISSIONS:", city_site.SUBMISSIONS)

    print("\n=== Scene 2: TV fee letter -> exemption")
    a.reset()
    await say(a, compose_message("tv_fee", ""), "[shows TV fee letter]")
    await say(a, "Yes, I get Grundsicherung im Alter.")

    print("\n=== Scene 3: fake fine")
    a.reset()
    await say(a, compose_message("fake_fine", "Oh no, I must pay this today! Help me."), "[shows fake fine] Oh no, I must pay this today! Help me.")

    print("\n=== Scene 4: tax letter, asked in Turkish")
    a.reset()
    await say(a, compose_message("tax", "Bu mektup ne diyor? Annemin bakımı için para ödedim."), "[shows tax letter] (Turkish question)")
    print("\nSUBMISSIONS:", city_site.SUBMISSIONS)
    await b.stop()

asyncio.run(main())
