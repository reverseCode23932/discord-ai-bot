"""Text-to-speech backends."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from discord_ai.i18n.languages import LanguagePreset
from discord_ai.logging_setup import get_logger

log = get_logger("tts")

SynthesizerName = Literal["edge", "gtts"]
MAX_TTS_CHARS = 500


async def synthesize(
    text: str,
    out_path: Path,
    *,
    engine: SynthesizerName,
    preset: LanguagePreset,
    edge_voice: str | None = None,
) -> Path:
    snippet = text[:MAX_TTS_CHARS].strip()
    if not snippet:
        raise ValueError("Nothing to speak.")

    voice = edge_voice or preset.edge_voice
    log.debug(
        "Synthesize engine=%s lang=%s voice=%s chars=%d",
        engine,
        preset.code,
        voice if engine == "edge" else preset.gtts_lang,
        len(snippet),
    )

    if engine == "edge":
        return await _edge(snippet, out_path, voice)
    if engine == "gtts":
        return await _gtts(snippet, out_path, preset.gtts_lang)
    raise ValueError(f"Unknown synthesizer: {engine}")


async def _edge(text: str, out_path: Path, voice: str) -> Path:
    import edge_tts

    await edge_tts.Communicate(text, voice).save(str(out_path))
    log.debug("Edge TTS done: %s", out_path.name)
    return out_path


async def _gtts(text: str, out_path: Path, lang: str) -> Path:
    from gtts import gTTS

    def _run() -> None:
        gTTS(text=text, lang=lang).save(str(out_path))

    await asyncio.to_thread(_run)
    log.debug("gTTS done: %s", out_path.name)
    return out_path
