# Discord AI Bot

A Discord bot with **AI chat** (OpenAI, **Ollama**, **Groq**, or custom), **per-user language** settings, voice listen (local Whisper STT), and TTS in voice channels.

Uses an **official Discord bot token** from the [Developer Portal](https://discord.com/developers/applications) — not a personal account token.

## Features

- Slash commands: `/ask`, `/say`, `/askvoice`, `/listen`, `/stoplisten`, `/language`, `/synthesizer`, `/voice`, `/settings`, `/reset`, `/leave`
- **Voice listen**: join VC, hear your speech → Whisper STT → AI → optional TTS reply
- Prefix commands: `!ask`, `!lang`, `!reset`
- Mention or prefix triggers in text channels
- Per-user language (en, ru, uk, de, fr, es, pt, ja, zh, pl, tr)
- Two TTS engines: **edge** (neural) and **gtts** (Google)
- Per-channel conversation memory
- Rotating logs in `data/logs/bot.log`

## Requirements

- **Python 3.10+**
- **FFmpeg** (for voice playback) — [install guide](https://ffmpeg.org/download.html)
- **Discord bot application** + token
- **LLM backend**: [Ollama](https://ollama.com) (free/local), [Groq](https://groq.com) (free tier), or OpenAI

## Quick start

```powershell
git clone https://github.com/reverseCode23932/discord-ai-bot.git
cd discord-ai-bot

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Voice also needs FFmpeg on PATH and davey (included in requirements.txt)

copy .env.example .env
# Edit .env — add DISCORD_BOT_TOKEN and LLM settings (see below)

python run.py
```

## Discord setup

### 1. Create the application

1. Open [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. **Bot** → **Reset Token** → copy into `.env` as `DISCORD_BOT_TOKEN`
3. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent** (required for `@mentions` and `!` prefix commands)

### 2. Bot permissions (server)

Enable these **Bot Permissions** when generating the invite link:

| Permission | Why |
|------------|-----|
| View Channels | See channels to reply |
| Send Messages | Post AI replies |
| Read Message History | Context in channels |
| Connect | Join voice for TTS |
| Speak | Play TTS audio in voice |

**Optional** (not required): Embed Links, Attach Files.

**Permission integer** (for manual invite URLs): `3214336`

### 3. OAuth2 scopes

In **OAuth2 → URL Generator**, select:

| Scope | Required |
|-------|----------|
| `bot` | Yes |
| `applications.commands` | Yes (slash commands) |

Then select the five permissions above and open the generated URL to invite the bot to your server.

Example invite URL shape:

```text
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=3214336&scope=bot%20applications.commands
```

Replace `YOUR_CLIENT_ID` with **Application ID** (General Information).

### 4. Make it feel personal (optional)

In the Developer Portal → **Bot**, set **username** and **avatar** to match your style. This is the supported way to customize appearance — do not use a user account token.

## Environment variables

Copy `.env.example` to `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Bot token from Developer Portal |
| `LLM_PROVIDER` | No | `ollama` (default), `groq`, `openai`, `custom` |
| `LLM_MODEL` | No | e.g. `llama3.2`, `llama-3.1-8b-instant`, `gpt-4o-mini` |
| `LLM_API_KEY` | If groq/openai | API key (Groq or OpenAI) |
| `LLM_BASE_URL` | If custom/ollama | e.g. `http://127.0.0.1:11434/v1` |
| `BOT_PREFIX` | No | Default `!` |
| `DEFAULT_LANGUAGE` | No | Default `en` for new users |
| `DEFAULT_SYNTHESIZER` | No | `edge` or `gtts` |
| `LOG_LEVEL` | No | `INFO` or `DEBUG` |
| `LOG_TO_FILE` | No | `true` / `false` |
| `LOG_MAX_BYTES` | No | Max log file size (bytes) |
| `VOICE_WAKE_WORDS` | No | Comma-separated wake phrase(s) for `/listen` |
| `VOICE_REPLY_TTS` | No | Speak AI replies in voice (`true`/`false`) |
| `VOICE_REPLY_TEXT` | No | Post heard text + reply in chat (whisper-style) |
| `CHAT_WHISPER_DELETE_AFTER` | No | Auto-delete voice chat replies after N seconds (`90`) |
| `CHAT_EPHEMERAL` | No | Slash replies only visible to you (`true`) |
| `STT_ENGINE` | No | `local` (default), `google`, `openai`, `auto` |
| `WHISPER_LOCAL_MODEL` | No | `small` (default), `base`, `medium`, `tiny` |
| `WHISPER_DEVICE` | No | `cpu` or `cuda` (GPU) |
| `WHISPER_COMPUTE_TYPE` | No | `int8` on CPU, `float16` on GPU |
| `WHISPER_BEAM_SIZE` | No | Higher = more accurate, slower (default `5`) |
| `WHISPER_VAD_FILTER` | No | Skip silence/noise (`true`) |
| `LLM_TIMEOUT_SECONDS` | No | Max wait for Ollama/Groq reply (default `180`) |
| `MIN_SPEECH_BYTES` | No | Min audio before STT (default ~0.4s) |

## Commands

| Command | Description |
|---------|-------------|
| `/ask` | Ask the AI (your language) |
| `/say` | Speak text in your voice channel |
| `/askvoice` | AI reply + speak in voice |
| `/language` | Set or list languages |
| `/synthesizer` | `edge` or `gtts` |
| `/voice` | Pick Edge TTS voice |
| `/settings` | Show your preferences |
| `/reset` | Clear channel chat history |
| `/listen` | Join your VC and listen for spoken commands |
| `/stoplisten` | Stop voice listening |
| `/leave` | Disconnect from voice and stop listening |

## LLM without OpenAI (quota / billing)

### Option A — Ollama (local, free)

1. Install [Ollama](https://ollama.com/download)
2. In a terminal:

   ```powershell
   ollama serve
   ollama pull llama3.2
   ```

3. In `.env`:

   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.2
   STT_ENGINE=local
   ```

### Option B — Groq (cloud, free tier)

1. Get a key at https://console.groq.com  
2. In `.env`:

   ```env
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_your_key_here
   LLM_MODEL=llama-3.1-8b-instant
   ```

### Option C — LM Studio (local GUI)

1. Load a model in LM Studio → start server  
2. In `.env`:

   ```env
   LLM_PROVIDER=custom
   LLM_BASE_URL=http://127.0.0.1:1234/v1
   LLM_API_KEY=lm-studio
   LLM_MODEL=name-shown-in-lm-studio
   ```

## Voice commands (`/listen`)

1. Join a voice channel.
2. Run `/listen` in a text channel (same server).
3. Wait for the bot to join, then speak when Discord shows your **green speaking indicator**.
4. The bot transcribes speech → asks the LLM → posts a short **chat whisper** (auto-deletes) and optionally **speaks** the reply in voice.

Optional in `.env`:

- `VOICE_WAKE_WORDS=hey bot` — only react after that phrase (comma-separated for multiple).
- `VOICE_WAKE_WORDS=` (empty) — react to any speech.
- Say **"стоп"** / **"stop listening"** or use `/stoplisten` to end.

Requires: `discord-ext-voice-recv`, `davey`, FFmpeg, and `faster-whisper` (local STT — **no OpenAI key**).

## Speech recognition tips (Whisper)

The bot uses **local [faster-whisper](https://github.com/SYSTRAN/faster-whisper)** by default (`STT_ENGINE=local`). Discord audio is converted to **mono 16 kHz** before transcription for better accuracy.

### Pick a model size

| Model | Speed | Russian accuracy | RAM (approx.) |
|-------|-------|------------------|---------------|
| `tiny` | Fastest | Poor (hallucinations on silence) | ~1 GB |
| `base` | Fast | OK | ~1 GB |
| **`small`** | Medium | **Recommended** (default) | ~2 GB |
| `medium` | Slow | Best local quality | ~5 GB |

In `.env`:

```env
STT_ENGINE=local
WHISPER_LOCAL_MODEL=small
WHISPER_VAD_FILTER=true
WHISPER_BEAM_SIZE=5
```

First run downloads the model (~500 MB for `small`). Check logs:

```text
Loading local Whisper 'small' (device=cpu compute=int8...)
local STT (12 chars): привет как дела
```

### `.env` gotchas

- **Do not duplicate** `WHISPER_LOCAL_MODEL` — if it appears twice, only the **first** line wins (dotenv default). Keep one line.
- Set `/language ru` (or your code) so Whisper uses the right language hint.
- If recognition is still weak, try `WHISPER_LOCAL_MODEL=medium` or enable GPU:

  ```env
  WHISPER_DEVICE=cuda
  WHISPER_COMPUTE_TYPE=float16
  ```

### Speaking tips

- Use a **headset mic**; avoid music or TV in the background.
- Speak **1–2 seconds** after the green ring appears; pause briefly between phrases.
- Wait for Ollama on CPU — the first reply can take **30–60+ seconds**; do not `/stoplisten` too early.

### Alternative: Google STT (no local model download)

Requires internet; often good for short Russian phrases:

```env
STT_ENGINE=google
```

Install: `pip install SpeechRecognition`

## Project structure

```text
discord-ai-bot/
├── run.py                 # Entry point
├── requirements.txt
├── .env.example
├── data/                  # Runtime data (gitignored)
│   ├── user_settings.json
│   └── logs/bot.log
└── src/discord_ai/
    ├── main.py
    ├── config.py
    ├── logging_setup.py
    ├── bot/client.py
    ├── commands/          # slash + prefix
    ├── services/          # ai, voice, listen, stt, settings, history
    ├── i18n/languages.py
    └── tts/synthesizer.py
```

## Logging

Logs go to the console and `data/logs/bot.log` (rotating, 5 backups).

Set `LOG_LEVEL=DEBUG` to log full prompts and replies.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot does not reply to `!ask` | Enable **Message Content Intent** in Developer Portal |
| Slash commands missing | Re-invite with `applications.commands` scope; wait ~1 min after start |
| Voice error **4017** / cannot join VC | `pip install davey` and `discord.py>=2.7` |
| `/listen` does nothing | Install `discord-ext-voice-recv`; speak when green ring shows |
| `OpusError: corrupted stream` | Reinstall deps from `requirements.txt` (DAVE-patched voice-recv fork) |
| Voice silent / no audio | Install FFmpeg and ensure it is on `PATH`; wait for LLM (check logs for `LLM reply`) |
| Wrong / nonsense transcription | Use `WHISPER_LOCAL_MODEL=small` or `medium`; remove duplicate `.env` lines; see [Speech recognition tips](#speech-recognition-tips-whisper) |
| Hallucinations like «Редактор субтитров» | Normal for `tiny` on silence — upgrade model; bot filters common phrases |
| `Missing env vars` | Create `.env` from `.env.example` |
| OpenAI 429 / quota | Switch to `LLM_PROVIDER=ollama` or `groq`; use `STT_ENGINE=local` |
| Ollama connection / no voice reply | Run `ollama serve` and `ollama pull llama3.2`; increase `LLM_TIMEOUT_SECONDS` |
| `gh` not recognized | Close/reopen terminal or use full path to `gh.exe` (see below) |

## GitHub — clone, update, and push

### Clone this repo

```powershell
git clone https://github.com/reverseCode23932/discord-ai-bot.git
cd discord-ai-bot
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — never commit real tokens
```

### Daily workflow (after you change code)

```powershell
cd C:\path\to\discord-ai-bot
git status
git add .
git commit -m "describe your change"
git push
```

**Never commit `.env`** — it is gitignored. Only commit `.env.example` with placeholders.

### First-time publish (new fork)

1. Install [GitHub CLI](https://cli.github.com/) (`winget install GitHub.cli`)
2. Log in:

   ```powershell
   cd C:\Users\Gleb\discord-ai-bot
   .\scripts\gh-login.ps1
   ```

   Or:

   ```powershell
   & "C:\Program Files\GitHub CLI\gh.exe" auth login
   ```

   **If `gh` is not recognized:** close and reopen PowerShell, or use the scripts in `scripts/`.

3. Create repo and push:

   ```powershell
   .\scripts\publish-to-github.ps1
   ```

   Or manually:

   ```powershell
   git remote add origin https://github.com/<your-username>/discord-ai-bot.git
   git branch -M main
   git push -u origin main
   ```

### Pull updates from GitHub

```powershell
git pull origin main
pip install -r requirements.txt
```

If you use a venv in another folder (e.g. `Envs\dsbot`), activate it and reinstall there too.

### Issues & contributions on GitHub

- **Bug reports:** open an [Issue](https://github.com/reverseCode23932/discord-ai-bot/issues) with logs from `data/logs/bot.log` (remove your bot token first).
- **Pull requests:** fork → branch → commit → PR. Keep changes focused; do not include `.env` or `data/`.

## License

MIT — see [LICENSE](LICENSE).
