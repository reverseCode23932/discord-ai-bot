"""Central logging configuration (console + rotating file)."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from discord_ai.config import DATA_DIR, LOG_LEVEL, LOG_MAX_BYTES, LOG_TO_FILE

LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "bot.log"

_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = LOG_LEVEL.upper()
    level = getattr(logging, level_name, logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger("discord_ai")
    root.setLevel(level)
    root.handlers.clear()
    root.propagate = False

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    if LOG_TO_FILE:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    # Harmless RTCP sender reports — very noisy at INFO during /listen
    logging.getLogger("discord.ext.voice_recv").setLevel(logging.WARNING)
    logging.getLogger("discord.ext.voice_recv.reader").setLevel(logging.WARNING)
    logging.getLogger("discord.ext.voice_recv.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.ext.voice_recv.opus").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)

    _CONFIGURED = True
    root.info("Logging initialized (level=%s, file=%s)", level_name, LOG_TO_FILE)


def get_logger(name: str) -> logging.Logger:
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(f"discord_ai.{name}")
