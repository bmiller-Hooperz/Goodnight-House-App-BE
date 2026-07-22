# Goodnight House — Chat Backend (Phase 1)

This is the AI chat API for the Goodnight House app. It answers parent questions using Jessie’s sleep library (RAG) plus a family’s plan context.

**Phase 1 note:** The mobile app currently sends **mock Oliver family data**. The library and system prompt are real.

---

## What you need before starting

1. A computer (Mac is assumed below)
2. An [OpenRouter](https://openrouter.ai/) account and API key (for the AI model)
3. This repo downloaded (see below)
4. The Goodnight House **mobile app** repo if you want to chat from the app UI

You do **not** need to know Python deeply. Follow the steps in order.

---

## 1. Install Python (one-time)

1. Open **Terminal** (Spotlight → type `Terminal` → Enter)
2. Check if Python is installed:

```bash
python3 --version
```

You want something like `Python 3.11` or `3.12` or `3.13`.

If that command fails, install Python from [https://www.python.org/downloads/](https://www.python.org/downloads/) (check “Add Python to PATH” if on Windows), then quit and reopen Terminal.

---

## 2. Download this project

### Option A — GitHub Desktop (easiest)

1. Install [GitHub Desktop](https://desktop.github.com/)
2. File → Clone repository → find `Goodnight-House-App-BE`
3. Note the folder it saves to (you’ll need that path)

### Option B — Terminal

```bash
cd ~/Documents
git clone https://github.com/bmiller-Hooperz/Goodnight-House-App-BE.git
cd Goodnight-House-App-BE
```

---

## 3. Create a “virtual environment” (one-time)

A virtual environment is just a private folder of Python packages for this project so nothing messes with the rest of your computer.

In Terminal, go into the project folder (adjust the path if yours is different):

```bash
cd ~/Documents/Goodnight-House-App-BE
```

Then run:

```bash
python3 -m venv .venv
```

That creates a folder named `.venv`. You only do this once.

---

## 4. Turn the virtual environment on

Every time you open a **new** Terminal window to work on this project, run:

```bash
cd ~/Documents/Goodnight-House-App-BE
source .venv/bin/activate
```

When it’s on, you should see `(.venv)` at the start of your Terminal line.

To turn it off later (optional):

```bash
deactivate
```

---

## 5. Install the project packages (one-time, or after updates)

With `(.venv)` active:

```bash
pip install -r requirements.txt
```

The first time may take a couple of minutes.

---

## 6. Add your OpenRouter API key

1. In the project folder, copy the example env file:

```bash
cp .env.example .env
```

2. Open `.env` in any text editor (TextEdit, VS Code, Cursor, etc.)
3. Set your key (no quotes):

```bash
OPENROUTER_API_KEY=sk-or-v1-paste-your-real-key-here
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
```

4. Save the file

**Important:** Never commit `.env` or send your key in Slack/email screenshots if you can avoid it. `.env` is gitignored on purpose.

---

## 7. Build the search index (one-time)

This turns Jessie’s library into a searchable local index (Chroma). First run downloads a small local embedding model (~80MB).

With `(.venv)` active:

```bash
python -m app.indexer
```

You should see something like `"indexed": 277`.

---

## 8. Start the server

With `(.venv)` active:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or:

```bash
./scripts/run_server.sh
```

Leave this Terminal window open. When it’s running you should see something like `Application startup complete`.

### Quick check

Open a browser and go to:

[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

You want JSON like:

```json
{
  "ok": true,
  "indexed_resources": 277,
  "model": "deepseek/deepseek-v4-flash",
  "has_api_key": true
}
```

If `has_api_key` is `false`, fix `.env` and restart the server (Ctrl+C, then start again).

---

## 9. Use it with the mobile app

1. Keep this server running
2. In the Goodnight House Expo app, open the **Chat** tab
3. Ask questions (Oliver’s mock plan is what the app sends today)

On an iPhone Simulator, the app talks to `http://127.0.0.1:8000` by default.

---

## Stopping the server

In the Terminal where the server is running, press:

`Control + C`

---

## Common problems

| What you see | What to try |
| --- | --- |
| `command not found: python3` | Install Python, reopen Terminal |
| `command not found: pip` | Make sure you ran `source .venv/bin/activate` first |
| `has_api_key: false` | Check `.env` has a real `OPENROUTER_API_KEY`, restart server |
| Chat says it can’t reach the API | Server isn’t running, or wrong URL / device needs your computer’s LAN IP |
| `401` / model errors from OpenRouter | Check key, credits, and `OPENROUTER_MODEL` on [openrouter.ai](https://openrouter.ai/) |
| Port already in use | Something else is on 8000 — stop it, or use `--port 8001` and update the app URL |

---

## What this backend does (short)

1. Loads Jessie’s fixed **system prompt** + **always-on** app/plan text
2. Searches the **content library** for relevant resources (`retrieve_when` → `body`)
3. Sends those resources + the family’s plan context to the AI model
4. Returns a reply plus `resource_…` citations

It does **not** redesign a family’s plan. It coaches from the plan + library.

---

## Useful commands (cheat sheet)

```bash
cd ~/Documents/Goodnight-House-App-BE
source .venv/bin/activate
pip install -r requirements.txt
python -m app.indexer
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
