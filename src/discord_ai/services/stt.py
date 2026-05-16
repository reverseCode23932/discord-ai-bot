"""Speech-to-text: OpenAI Whisper with optional Google fallback."""

from __future__ import annotations

import asyncio
from pathlib import Path

from openai import OpenAI, RateLimitError

from discord_ai.config import OPENAI_API_KEY, STT_ENGINE
from discord_ai.logging_setup import get_logger

log = get_logger("stt")

_client: OpenAI | None = None

# Maps our language codes to SpeechRecognition / Google locale hints
_GOOGLE_LANG: dict[str, str] = {
    "en": "en-US",
    "ru": "ru-RU",
    "uk": "uk-UA",
    "de": "de-DE",
    "fr": "fr-FR",
    "es": "es-ES",
    "pt": "pt-BR",
    "ja": "ja-JP",
    "zh": "zh-CN",
    "pl": "pl-PL",
    "tr": "tr-TR",
}


class STTQuotaError(Exception):
    """OpenAI billing/quota blocks Whisper."""


def init_stt() -> None:
    global _client
    _client = OpenAI(api_key=OPENAI_API_KEY)


def _openai_transcribe(wav_path: Path, language: str | None) -> str:
    if _client is None:
        raise RuntimeError("STT client not initialized")
    with wav_path.open("rb") as audio_file:
        kwargs: dict = {"model": "whisper-1", "file": audio_file}
        if language:
            kwargs["language"] = language
        result = _client.audio.transcriptions.create(**kwargs)
    return (result.text or "").strip()


def _google_transcribe(wav_path: Path, language: str | None) -> str:
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    google_lang = _GOOGLE_LANG.get(language or "en", "en-US")
    with sr.AudioFile(str(wav_path)) as source:
        audio = recognizer.record(source)
    text = recognizer.recognize_google(audio, language=google_lang)
    return (text or "").strip()


def _is_quota_error(exc: RateLimitError) -> bool:
    body = getattr(exc, "body", None) or {}
    if isinstance(body, dict):
        err = body.get("error") or {}
        if err.get("code") == "insufficient_quota":
            return True
        if err.get("type") == "insufficient_quota":
            return True
    return "insufficient_quota" in str(exc).lower() or "quota" in str(exc).lower()


async def transcribe_wav(wav_path: Path, *, language: str | None = None) -> str:
    engine = STT_ENGINE

    if engine == "google":
        text = await asyncio.to_thread(_google_transcribe, wav_path, language)
        log.info("Google STT (%d chars): %s", len(text), text[:120])
        return text

    if engine == "openai":
        text = await asyncio.to_thread(_openai_transcribe, wav_path, language)
        log.info("Whisper STT (%d chars): %s", len(text), text[:120])
        return text

    # auto: OpenAI first, then Google on quota errors
    try:
        text = await asyncio.to_thread(_openai_transcribe, wav_path, language)
        log.info("Whisper STT (%d chars): %s", len(text), text[:120])
        return text
    except RateLimitError as exc:
        if not _is_quota_error(exc):
            raise
        log.warning("OpenAI STT quota hit — falling back to Google STT")
        try:
            text = await asyncio.to_thread(_google_transcribe, wav_path, language)
            log.info("Google STT fallback (%d chars): %s", len(text), text[:120])
            return text
        except Exception as fallback_exc:
            log.exception("Google STT fallback failed")
            raise STTQuotaError("OpenAI quota exhausted and Google STT failed") from fallback_exc
