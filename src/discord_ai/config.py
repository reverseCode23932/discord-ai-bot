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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")

BASE_SYSTEM_PROMPT = (
    "You are a helpful, concise Discord assistant. "
    "Keep replies short unless the user asks for detail. "
    "Use plain text; avoid markdown tables and huge code blocks."
)

MAX_HISTORY = 12
MAX_REPLY_CHARS = 1900


def require_env() -> list[str]:
    missing = []
    if not DISCORD_TOKEN:
        missing.append("DISCORD_BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    return missing
