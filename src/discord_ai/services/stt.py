"""Speech-to-text via OpenAI Whisper."""

from __future__ import annotations

import asyncio
from pathlib import Path

from openai import OpenAI

from discord_ai.config import OPENAI_API_KEY
from discord_ai.logging_setup import get_logger

log = get_logger("stt")

_client: OpenAI | None = None


def init_stt() -> None:
    global _client
    _client = OpenAI(api_key=OPENAI_API_KEY)


async def transcribe_wav(wav_path: Path, *, language: str | None = None) -> str:
    if _client is None:
        raise RuntimeError("STT client not initialized")

    def _call() -> str:
        with wav_path.open("rb") as audio_file:
            kwargs: dict = {"model": "whisper-1", "file": audio_file}
            if language:
                kwargs["language"] = language
            result = _client.audio.transcriptions.create(**kwargs)
        return (result.text or "").strip()

    text = await asyncio.to_thread(_call)
    log.info("Whisper transcript (%d chars): %s", len(text), text[:120])
    return text
