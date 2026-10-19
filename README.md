# Euron Voice Live Demo

A small FastAPI app that streams your microphone audio from the browser to the Euri Live API over a WebSocket and plays back the spoken response.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then put your EURI_API_KEY in .env
```

## Run

```bash
python server.py
```

Open http://127.0.0.1:8001 in your browser and allow microphone access.

## Environment variables

| Variable           | Required | Default                                          | Purpose                          |
|--------------------|----------|--------------------------------------------------|----------------------------------|
| `EURI_API_KEY`     | yes      | —                                                | Euri API key                     |
| `EURI_LIVE_URL`    | no       | `wss://api.euron.one/api/v1/euri/live/sessions`  | Euri Live websocket endpoint     |
| `EURI_LIVE_MODEL`  | no       | `gpt-live-1`                                     | Voice model (listens + speaks)   |
| `EURI_BRAIN_MODEL` | no       | `gpt-6-luna`                                     | Reasoning + web search model     |

`.env` is git-ignored — never commit your real key.
