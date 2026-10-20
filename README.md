# Euron Live Voice

A real-time voice assistant and tutor in your browser. Speak in any language (English, Hindi, Hinglish, Spanish, ...) and it answers out loud. Questions about news, prices or weather get a web search first.

## How it works

```
Browser (mic + speaker)  <-- WebSocket /ws -->  server.py  <-- WebSocket -->  EURI gpt-live-1
                                               (adds your API key)               |
                                                                                 +--> gpt-6-luna + web search
```

`server.py` is a small FastAPI relay. Browsers can't send an `Authorization` header on a WebSocket, and the API key should never reach the browser, so the server holds the key and forwards audio both ways.

| File               | What it does                                             |
|--------------------|----------------------------------------------------------|
| `server.py`        | FastAPI server: serves the page and relays `/ws` to EURI |
| `index.html`       | Front end: mic capture, audio playback, live transcript |
| `requirements.txt` | Python dependencies                                      |
| `.env.example`     | Template for your `.env` file                            |

## Requirements

- Python 3.10 or newer (built and tested with 3.12)
- A EURI API key from [euron.one](https://euron.one)
- Chrome or Edge, with a working microphone

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/euron-tech/Euron-voice-live-demo.git
cd Euron-voice-live-demo
```

### 2. Create and activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

**Windows (Command Prompt)**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

**Windows (PowerShell / CMD)**
```powershell
copy .env.example .env
```

**macOS / Linux**
```bash
cp .env.example .env
```

Open `.env` and set your key:

```env
EURI_API_KEY=your-real-euri-api-key
```

The other values are optional. Their defaults are listed in the table below.

## Run

```bash
python server.py
```

Then open **http://127.0.0.1:8001** in Chrome or Edge and allow microphone access when the browser asks.

Stop the server with `Ctrl + C`.

### Alternative: run with uvicorn (auto-reload while developing)

```bash
uvicorn server:app --host 127.0.0.1 --port 8001 --reload
```

This skips the startup check for `EURI_API_KEY`, so make sure your `.env` is filled in first.

## Using the app

| Action                | Control                               |
|-----------------------|---------------------------------------|
| Start / stop talking  | Main button, or the `Space` key       |
| Mute / unmute the mic | Mute button, or the `M` key           |
| Clear the transcript  | Clear button                          |

## Environment variables

| Variable           | Required | Default                                         | Purpose                         |
|--------------------|----------|-------------------------------------------------|---------------------------------|
| `EURI_API_KEY`     | yes      | none                                            | Your EURI API key               |
| `EURI_LIVE_URL`    | no       | `wss://api.euron.one/api/v1/euri/live/sessions` | EURI Live WebSocket endpoint    |
| `EURI_LIVE_MODEL`  | no       | `gpt-live-1`                                    | Voice model (listens + speaks)  |
| `EURI_BRAIN_MODEL` | no       | `gpt-6-luna`                                    | Reasoning + web search model    |

## Troubleshooting

- **`Add EURI_API_KEY to the .env file first`**: `.env` is missing, or the key is empty. Repeat step 4.
- **`EURI rejected the connection (HTTP 401)`**: the API key is missing, wrong or revoked. The message gives the exact reason. Put a valid key in `.env` and restart the server.
- **`EURI rejected the connection (HTTP 403)`**: the key was accepted, but your account isn't allowed to do this. Usually the plan doesn't include `gpt-live-1` / `gpt-6-luna`, or it's out of credits. Read the reason in the message, then check your plan at [euron.one/euri](https://euron.one/euri) or create a new key.
- **No microphone prompt or no audio**: use Chrome or Edge, and open the page at `127.0.0.1` or `localhost`. Browsers only allow the mic on secure origins, and those two count as secure.
- **`Address already in use`**: something else is using port 8001. Stop it, or run with uvicorn on another port, e.g. `--port 8002`.
- **Errors in the transcript**: check that your API key is valid and that the model names in `.env` are correct.

## Security

`.env` is listed in `.gitignore`. Never commit your real API key; put new variables in `.env.example` with placeholder values instead.
