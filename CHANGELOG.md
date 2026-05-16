# Changelog

## [1.0.0] — 2026-05-16

First stable release.

### Features

- Slash commands: `/ask`, `/say`, `/askvoice`, `/listen`, `/stoplisten`, `/language`, `/synthesizer`, `/voice`, `/settings`, `/reset`, `/leave`
- LLM backends: **Ollama** (default), Groq, OpenAI, custom OpenAI-compatible APIs
- Voice listen: hybrid **Google + Whisper** STT, optional **Edge TTS** replies in voice
- Per-user language and TTS settings (11 languages)
- NVIDIA GPU Whisper (`cuda` + `float16`) with CPU fallback
- Local logs in `data/logs/bot.log`

### Requirements

- Python 3.10+, FFmpeg, Discord bot token
- For GPU STT on Windows: `.\scripts\install-gpu-stt.ps1`
