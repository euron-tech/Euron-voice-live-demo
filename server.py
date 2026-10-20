"""Euron Live Voice - a tiny relay between your browser and EURI's gpt-live-1.

Browser (mic + speaker)  <-- WebSocket /ws -->  this server  <-- WebSocket -->  EURI gpt-live-1
                                                      (adds your API key)            |
                                                                                     +--> GPT-6 + web search

Why a relay? Browsers can't put an "Authorization" header on a WebSocket,
and your API key must never be sent to the browser anyway.
"""
import asyncio
import base64
import json
import os
from pathlib import Path

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

load_dotenv(Path(__file__).parent / ".env")

EURI_API_KEY = os.getenv("EURI_API_KEY", "").strip().strip('"\'')  # tolerate stray spaces/quotes in .env
EURI_LIVE_URL = os.getenv("EURI_LIVE_URL", "wss://api.euron.one/api/v1/euri/live/sessions")
LIVE_MODEL = os.getenv("EURI_LIVE_MODEL", "gpt-live-1")        # the voice model (listens + speaks)
BRAIN_MODEL = os.getenv("EURI_BRAIN_MODEL", "gpt-6-luna")       # does reasoning + web search

INSTRUCTIONS = """You are Euron Live, a friendly, real-time voice assistant and tutor.
- Always reply in the same language the user is speaking (Hindi, English, Hinglish, Spanish, anything).
- Keep spoken answers short and natural; offer to go deeper.
- For news, prices, weather or anything recent, search the web first.
- When teaching, explain step by step with simple examples and check if the user understood."""

app = FastAPI()


@app.get("/")
def home():
    return FileResponse(Path(__file__).parent / "index.html")


@app.websocket("/ws")
async def live(browser: WebSocket):
    await browser.accept()
    headers = {"Authorization": f"Bearer {EURI_API_KEY}"}

    try:
        async with websockets.connect(EURI_LIVE_URL, additional_headers=headers, max_size=None) as euri:
            # 1) Start a live session: gpt-live-1 talks, and hands hard questions to GPT-6 with web search.
            await euri.send(json.dumps({
                "type": "session.start",
                "session": {
                    "model": LIVE_MODEL,
                    "instructions": INSTRUCTIONS,
                    "delegation": {
                        "type": "responses",
                        "responses": {"model": BRAIN_MODEL, "tools": [{"type": "web_search"}]},
                    },
                },
            }))

            # 2) Browser -> EURI: raw 24 kHz 16-bit mono PCM chunks from the microphone.
            async def mic_to_euri():
                while True:
                    pcm = await browser.receive_bytes()
                    await euri.send(json.dumps({
                        "type": "session.input_audio.append",
                        "audio": base64.b64encode(pcm).decode(),
                    }))

            # 3) EURI -> Browser: AI voice, live transcripts and web-search progress (passed through as-is).
            async def euri_to_browser():
                async for message in euri:
                    await browser.send_text(message if isinstance(message, str) else message.decode())

            tasks = [asyncio.create_task(mic_to_euri()), asyncio.create_task(euri_to_browser())]
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)  # stop when either side hangs up
            for task in tasks:
                task.cancel()
            try:
                await euri.send(json.dumps({"type": "session.close"}))  # stop billing right away
            except websockets.ConnectionClosed:
                pass

    except WebSocketDisconnect:
        pass
    except Exception as error:
        message = describe_error(error)
        print("Live session error:", message)
        try:
            await browser.send_text(json.dumps({"type": "error", "error": {"message": message}}))
        except Exception:
            pass


def describe_error(error):
    """Turn a failed EURI handshake into a readable message (the reason is in the response body)."""
    if not isinstance(error, websockets.InvalidStatus):
        return str(error)
    status = error.response.status_code
    body = bytes(error.response.body or b"").decode(errors="replace")
    try:
        reason = json.loads(body)["error"]["message"]
    except (ValueError, KeyError, TypeError):
        reason = body[:300].strip() or "no details returned"
    hints = {
        401: "Check EURI_API_KEY in .env (missing, wrong or revoked), then restart the server.",
        403: "The key was accepted but is not allowed to use this. Check that your EURI plan includes "
             f"'{LIVE_MODEL}' / '{BRAIN_MODEL}' and has credits, or create a new key at https://euron.one/euri.",
    }
    hint = hints.get(status, "")
    return f"EURI rejected the connection (HTTP {status}): {reason}" + (f" -> {hint}" if hint else "")


if __name__ == "__main__":
    import uvicorn

    if not EURI_API_KEY:
        raise SystemExit("Add EURI_API_KEY to the .env file first (see README).")
    print("Open http://localhost:8001 in Chrome or Edge")
    uvicorn.run(app, host="127.0.0.1", port=8001)
