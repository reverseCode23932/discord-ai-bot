"""OpenAI chat completions."""

from __future__ import annotations

import asyncio
import time

from openai import OpenAI

from discord_ai.config import (
    BASE_SYSTEM_PROMPT,
    MAX_REPLY_CHARS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from discord_ai.i18n.languages import resolve_language
from discord_ai.logging_setup import get_logger
from discord_ai.services.history import history
from discord_ai.services.settings import settings

log = get_logger("ai")

_client: OpenAI | None = None


def init_openai() -> None:
    global _client
    _client = OpenAI(api_key=OPENAI_API_KEY)
    log.info("OpenAI client ready (model=%s)", OPENAI_MODEL)


def system_prompt_for(user_id: int) -> str:
    prefs = settings.get(user_id)
    lang = resolve_language(prefs.language)
    return f"{BASE_SYSTEM_PROMPT}\n\n{lang.prompt}"


async def ask_ai(channel_id: int, user_id: int, user_text: str) -> str:
    if _client is None:
        raise RuntimeError("OpenAI client not initialized")

    history.add(channel_id, "user", user_text)
    messages = [
        {"role": "system", "content": system_prompt_for(user_id)},
        *history.get(channel_id),
    ]

    log.info(
        "OpenAI request (user=%s channel=%s lang=%s prompt_len=%d)",
        user_id,
        channel_id,
        settings.get(user_id).language,
        len(user_text),
    )
    log.debug("User text: %s", user_text[:500])

    started = time.perf_counter()

    def _call() -> str:
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )
        return (response.choices[0].message.content or "").strip()

    try:
        reply = await asyncio.to_thread(_call)
    except Exception:
        log.exception("OpenAI call failed (user=%s channel=%s)", user_id, channel_id)
        raise

    elapsed_ms = (time.perf_counter() - started) * 1000
    if not reply:
        log.warning("Empty OpenAI reply (user=%s channel=%s)", user_id, channel_id)
        reply = "I couldn't generate a reply. Try again."

    history.add(channel_id, "assistant", reply)
    log.info(
        "OpenAI reply (user=%s channel=%s reply_len=%d elapsed_ms=%.0f)",
        user_id,
        channel_id,
        len(reply),
        elapsed_ms,
    )
    log.debug("Reply text: %s", reply[:500])
    return reply[:MAX_REPLY_CHARS]
