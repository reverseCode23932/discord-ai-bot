"""Application entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without installing the package (python run.py)
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from discord_ai.bot.client import AIBot
from discord_ai.commands import register_commands
from discord_ai.config import DISCORD_TOKEN, OPENAI_MODEL, require_env
from discord_ai.logging_setup import get_logger, setup_logging
from discord_ai.services.ai import init_openai
from discord_ai.services.stt import init_stt
from discord_ai.services.voice_deps import log_voice_dependency_status


def main() -> None:
    setup_logging()
    log = get_logger("main")

    missing = require_env()
    if missing:
        log.critical("Missing environment variables: %s", ", ".join(missing))
        raise SystemExit(
            f"Missing env vars: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in values."
        )

    log.info("Starting bot (model=%s)", OPENAI_MODEL)
    log_voice_dependency_status()
    init_openai()
    init_stt()
    bot = AIBot()
    register_commands(bot)
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
