# Discord AI Bot

A Discord bot that answers questions with **OpenAI**, supports **per-user language** settings, and can **speak in voice channels** using TTS (`edge-tts` or `gTTS`).

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
- **OpenAI API key**

## Quick start

```powershell
git clone https://github.com/reverseCode23932/discord-ai-bot.git
cd discord-ai-bot

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Voice also needs FFmpeg on PATH and davey (included in requirements.txt)

copy .env.example .env
# Edit .env — add DISCORD_BOT_TOKEN and OPENAI_API_KEY

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
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Default `gpt-4o-mini` |
| `BOT_PREFIX` | No | Default `!` |
| `DEFAULT_LANGUAGE` | No | Default `en` for new users |
| `DEFAULT_SYNTHESIZER` | No | `edge` or `gtts` |
| `LOG_LEVEL` | No | `INFO` or `DEBUG` |
| `LOG_TO_FILE` | No | `true` / `false` |
| `LOG_MAX_BYTES` | No | Max log file size (bytes) |
| `VOICE_WAKE_WORDS` | No | Comma-separated wake phrase(s) for `/listen` |
| `VOICE_REPLY_TTS` | No | Speak AI replies in voice (`true`/`false`) |
| `VOICE_REPLY_TEXT` | No | Post heard text + reply in chat |
| `MIN_SPEECH_BYTES` | No | Min audio before Whisper (default ~0.4s) |

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

## Voice commands (`/listen`)

1. Join a voice channel.
2. Run `/listen` in a text channel (same server).
3. Speak when Discord shows your **green speaking indicator**.
4. The bot transcribes your speech (OpenAI Whisper), asks the AI, then replies in text and voice.

Optional in `.env`:

- `VOICE_WAKE_WORDS=hey bot` — only react after that phrase (comma-separated for multiple).
- `VOICE_WAKE_WORDS=` (empty) — react to any speech.
- Say **"stop listening"** or use `/stoplisten` to end.

Requires: `discord-ext-voice-recv`, `davey`, FFmpeg, and OpenAI API (Whisper uses the same key).

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
| Voice silent / no audio | Install FFmpeg and ensure it is on `PATH` |
| `Missing env vars` | Create `.env` from `.env.example` |
| OpenAI errors | Check API key and billing on OpenAI dashboard |

## Publish to GitHub

Git is already initialized locally with an initial commit. To push to GitHub:

1. Install [GitHub CLI](https://cli.github.com/) (or `winget install GitHub.cli`)
2. Log in (works even if `gh` is not on PATH yet):

   ```powershell
   cd C:\Users\Gleb\discord-ai-bot
   .\scripts\gh-login.ps1
   ```

   Or use the full path after install:

   ```powershell
   & "C:\Program Files\GitHub CLI\gh.exe" auth login
   ```

   **If `gh` is not recognized:** close and reopen PowerShell, or use the scripts above.

3. Create the remote repo and push:

   ```powershell
   .\scripts\publish-to-github.ps1
   ```

   Or manually: create an empty repo on github.com, then:

   ```powershell
   git remote add origin https://github.com/<your-username>/discord-ai-bot.git
   git push -u origin main
   ```

## License

MIT — see [LICENSE](LICENSE).
