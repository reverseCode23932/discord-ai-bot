"""Environment and app constants."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"

load_dotenv(ROOT_DIR / ".env")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip()
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").strip().lower() in ("1", "true", "yes")
def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


LOG_MAX_BYTES = _int_env("LOG_MAX_BYTES", 5 * 1024 * 1024)

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()

# LLM — openai | ollama (local) | groq (free tier) | custom
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
if LLM_PROVIDER not in ("openai", "ollama", "groq", "custom"):
    LLM_PROVIDER = "ollama"

LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

if not LLM_MODEL:
    if LLM_PROVIDER == "ollama":
        LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    elif LLM_PROVIDER == "groq":
        LLM_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    else:
        LLM_MODEL = OPENAI_MODEL

LLM_API_KEY = os.getenv("LLM_API_KEY", OPENAI_API_KEY).strip()
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    os.getenv("OLLAMA_BASE_URL", ""),
).strip()

BOT_PREFIX = os.getenv("BOT_PREFIX", "!")

BASE_SYSTEM_PROMPT = (
    """chill guy, not a robot. answer like a human would. be concise. don't mention that you are an AI or a bot. if you don't know the answer, say you don't know. be honest. have fun! Also be helpful and answer the questions"""
)

MAX_HISTORY = 12
MAX_REPLY_CHARS = 1900

# Voice listen (STT) — comma-separated wake words; empty = react to any speech
_wake = os.getenv("VOICE_WAKE_WORDS", "").strip()
VOICE_WAKE_WORDS: tuple[str, ...] = tuple(w.strip() for w in _wake.split(",") if w.strip())

VOICE_REPLY_TTS = os.getenv("VOICE_REPLY_TTS", "true").strip().lower() in ("1", "true", "yes")

# ~0.4s of stereo 48kHz 16-bit PCM minimum before sending to Whisper
# ~0.5s stereo 48 kHz — slightly longer clips help Whisper
MIN_SPEECH_BYTES = _int_env("MIN_SPEECH_BYTES", 96_000)

# hybrid = Google first (often best for RU), then Whisper | google | local | auto
STT_ENGINE = os.getenv("STT_ENGINE", "hybrid").strip().lower()
if STT_ENGINE not in ("openai", "google", "local", "auto", "hybrid"):
    STT_ENGINE = "hybrid"

# Capture audio briefly after you stop speaking (Discord sends late packets)
VOICE_POST_ROLL_MS = _int_env("VOICE_POST_ROLL_MS", 400)

# tiny/base=fast | small=balanced | medium=clearest (good on RTX GPU)
_whisper_model = os.getenv("WHISPER_LOCAL_MODEL", "medium").strip().lower() or "medium"
WHISPER_LOCAL_MODEL = _whisper_model

# cpu | cuda | auto (try GPU, fall back to CPU)
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto").strip().lower() or "auto"
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "").strip()
if not WHISPER_COMPUTE_TYPE:
    WHISPER_COMPUTE_TYPE = "float16" if WHISPER_DEVICE in ("cuda", "gpu", "auto") else "int8"
WHISPER_BEAM_SIZE = _int_env("WHISPER_BEAM_SIZE", 8)
WHISPER_INITIAL_PROMPT = os.getenv("WHISPER_INITIAL_PROMPT", "").strip()
WHISPER_VAD_FILTER = os.getenv("WHISPER_VAD_FILTER", "true").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Min seconds between processing voice utterances (anti-spam)
VOICE_UTTERANCE_COOLDOWN = _int_env("VOICE_UTTERANCE_COOLDOWN", 3)

# Error notice cooldown in text channel during listen
VOICE_ERROR_COOLDOWN = _int_env("VOICE_ERROR_COOLDOWN", 60)

# LLM request timeout (Ollama on CPU can be slow)
LLM_TIMEOUT_SECONDS = _int_env("LLM_TIMEOUT_SECONDS", 180)

# Slash replies only visible to the user who ran the command
CHAT_EPHEMERAL = os.getenv("CHAT_EPHEMERAL", "true").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Voice: post heard + reply in text (auto-delete = "whisper" style)
VOICE_REPLY_TEXT = os.getenv("VOICE_REPLY_TEXT", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)
CHAT_WHISPER_DELETE_AFTER = _int_env("CHAT_WHISPER_DELETE_AFTER", 90)

# Edge neural TTS — slightly slower + louder = clearer in Discord voice
EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "-10%").strip() or "-10%"
EDGE_TTS_VOLUME = os.getenv("EDGE_TTS_VOLUME", "+12%").strip() or "+12%"
EDGE_TTS_PITCH = os.getenv("EDGE_TTS_PITCH", "+0Hz").strip() or "+0Hz"
DEFAULT_EDGE_VOICE = os.getenv("DEFAULT_EDGE_VOICE", "").strip()

# FFmpeg filters applied when playing TTS in voice channels
FFMPEG_PCM_OPTIONS = os.getenv(
    "FFMPEG_PCM_OPTIONS",
    "-filter:a aresample=48000,highpass=f=100,lowpass=f=14000,volume=1.25",
).strip()


def require_env() -> list[str]:
    missing = []
    if not DISCORD_TOKEN:
        missing.append("DISCORD_BOT_TOKEN")
    if LLM_PROVIDER in ("openai", "groq", "custom") and not LLM_API_KEY:
        missing.append("LLM_API_KEY (or OPENAI_API_KEY)")
    if LLM_PROVIDER == "custom" and not LLM_BASE_URL:
        missing.append("LLM_BASE_URL")
    return missing
