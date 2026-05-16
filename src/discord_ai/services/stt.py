"""Speech-to-text: OpenAI, Google, or local faster-whisper (no API key)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from openai import OpenAI, RateLimitError

from discord_ai.config import (
    OPENAI_API_KEY,
    STT_ENGINE,
    WHISPER_BEAM_SIZE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_LOCAL_MODEL,
    WHISPER_VAD_FILTER,
)
from discord_ai.logging_setup import get_logger

log = get_logger("stt")

_client: OpenAI | None = None
_local_model: object | None = None
_local_device: str = ""
_local_compute: str = ""
_openai_stt_disabled = False

# Skip segments Whisper thinks are non-speech (reduces garbage on noise)
_NO_SPEECH_PROB_MAX = 0.55

_HAS_GOOGLE: bool | None = None
_HAS_LOCAL: bool | None = None

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
    """No working STT backend available."""


class STTNotConfiguredError(Exception):
    """Requested STT engine is not installed."""


def _probe_google() -> bool:
    global _HAS_GOOGLE
    if _HAS_GOOGLE is None:
        try:
            import speech_recognition  # noqa: F401

            _HAS_GOOGLE = True
        except ImportError:
            _HAS_GOOGLE = False
    return _HAS_GOOGLE


def _probe_local() -> bool:
    global _HAS_LOCAL
    if _HAS_LOCAL is None:
        try:
            import faster_whisper  # noqa: F401

            _HAS_LOCAL = True
        except ImportError:
            _HAS_LOCAL = False
    return _HAS_LOCAL


def available_stt_backends() -> list[str]:
    backends: list[str] = []
    if OPENAI_API_KEY:
        backends.append("openai")
    if _probe_google():
        backends.append("google")
    if _probe_local():
        backends.append(f"local({WHISPER_LOCAL_MODEL})")
    return backends


def init_stt() -> None:
    global _client
    _client = None

    # Only connect to OpenAI when Whisper API may be used (not needed for local-only STT)
    if STT_ENGINE == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY required when STT_ENGINE=openai")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    elif STT_ENGINE == "auto" and OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY)

    backends = available_stt_backends()
    log.info("STT engine=%s, available backends: %s", STT_ENGINE, ", ".join(backends) or "none")
    if STT_ENGINE in ("google", "auto") and not _probe_google():
        log.warning("Google STT unavailable — pip install SpeechRecognition")
    if STT_ENGINE in ("local", "auto") and not _probe_local():
        log.warning("Local STT unavailable — pip install faster-whisper")
    if STT_ENGINE == "local":
        log.info("STT uses local Whisper only — no OpenAI key required")


def _openai_transcribe(wav_path: Path, language: str | None) -> str:
    global _openai_stt_disabled
    if _openai_stt_disabled:
        raise STTQuotaError("OpenAI STT skipped (quota previously exhausted)")

    if _client is None:
        raise STTNotConfiguredError(
            "OpenAI Whisper not configured. Set STT_ENGINE=local or add OPENAI_API_KEY"
        )

    with wav_path.open("rb") as audio_file:
        kwargs: dict = {"model": "whisper-1", "file": audio_file}
        if language:
            kwargs["language"] = language
        result = _client.audio.transcriptions.create(**kwargs)
    return (result.text or "").strip()


def _google_transcribe(wav_path: Path, language: str | None) -> str:
    if not _probe_google():
        raise STTNotConfiguredError("pip install SpeechRecognition")

    import speech_recognition as sr

    recognizer = sr.Recognizer()
    google_lang = _GOOGLE_LANG.get(language or "en", "en-US")
    with sr.AudioFile(str(wav_path)) as source:
        audio = recognizer.record(source)
    text = recognizer.recognize_google(audio, language=google_lang)
    return (text or "").strip()


def _is_cuda_runtime_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in (
            "cublas",
            "cudnn",
            "cuda",
            "cudart",
            "out of memory",
            "no cuda",
        )
    )


def _load_whisper_model(device: str, compute_type: str):
    from faster_whisper import WhisperModel

    log.info(
        "Loading local Whisper '%s' (device=%s compute=%s; first run may download)...",
        WHISPER_LOCAL_MODEL,
        device,
        compute_type,
    )
    return WhisperModel(
        WHISPER_LOCAL_MODEL,
        device=device,
        compute_type=compute_type,
    )


def _reset_local_model() -> None:
    global _local_model, _local_device, _local_compute
    _local_model = None
    _local_device = ""
    _local_compute = ""


def _get_local_model():
    global _local_model, _local_device, _local_compute
    if _local_model is not None:
        return _local_model

    device = WHISPER_DEVICE
    compute = WHISPER_COMPUTE_TYPE

    if device in ("cuda", "gpu"):
        try:
            _local_model = _load_whisper_model("cuda", compute)
            _local_device = "cuda"
            _local_compute = compute
            return _local_model
        except Exception as exc:
            if not _is_cuda_runtime_error(exc):
                raise
            log.warning(
                "CUDA Whisper failed (%s) — falling back to CPU. "
                "Install CUDA 12 + cuBLAS or set WHISPER_DEVICE=cpu in .env",
                exc,
            )
            _reset_local_model()

    _local_model = _load_whisper_model("cpu", "int8")
    _local_device = "cpu"
    _local_compute = "int8"
    if device in ("cuda", "gpu"):
        log.info("Whisper running on CPU (int8). Set WHISPER_DEVICE=cpu to skip CUDA attempt.")
    return _local_model


def _collect_transcript(segments, info, language: str | None) -> str:
    parts: list[str] = []
    for segment in segments:
        no_speech = getattr(segment, "no_speech_prob", 0.0) or 0.0
        if no_speech > _NO_SPEECH_PROB_MAX:
            log.debug("Skipped segment (no_speech_prob=%.2f): %s", no_speech, segment.text[:40])
            continue
        text = segment.text.strip()
        if text:
            parts.append(text)

    prob = getattr(info, "language_probability", None)
    if prob is not None:
        log.debug(
            "Whisper lang=%s prob=%.2f duration=%.2fs device=%s",
            getattr(info, "language", language),
            prob,
            getattr(info, "duration", 0.0),
            _local_device,
        )
    return " ".join(parts).strip()


def _local_transcribe(wav_path: Path, language: str | None) -> str:
    if not _probe_local():
        raise STTNotConfiguredError("pip install faster-whisper")

    kwargs: dict = {
        "beam_size": WHISPER_BEAM_SIZE,
        "vad_filter": WHISPER_VAD_FILTER,
        "condition_on_previous_text": False,
        "temperature": 0.0,
    }
    if language:
        kwargs["language"] = language

    try:
        model = _get_local_model()
        segments, info = model.transcribe(str(wav_path), **kwargs)
        return _collect_transcript(segments, info, language)
    except RuntimeError as exc:
        if _local_device != "cuda" or not _is_cuda_runtime_error(exc):
            raise
        log.warning("Whisper CUDA runtime error during transcribe — retrying on CPU")
        _reset_local_model()
        model = _get_local_model()
        segments, info = model.transcribe(str(wav_path), **kwargs)
        return _collect_transcript(segments, info, language)


def _is_quota_error(exc: RateLimitError) -> bool:
    body = getattr(exc, "body", None) or {}
    if isinstance(body, dict):
        err = body.get("error") or {}
        if err.get("code") == "insufficient_quota":
            return True
        if err.get("type") == "insufficient_quota":
            return True
    return "insufficient_quota" in str(exc).lower() or "quota" in str(exc).lower()


async def _run(engine: str, wav_path: Path, language: str | None) -> str:
    if engine == "openai":
        return await asyncio.to_thread(_openai_transcribe, wav_path, language)
    if engine == "google":
        return await asyncio.to_thread(_google_transcribe, wav_path, language)
    if engine == "local":
        return await asyncio.to_thread(_local_transcribe, wav_path, language)
    raise ValueError(f"Unknown STT engine: {engine}")


async def transcribe_wav(wav_path: Path, *, language: str | None = None) -> str:
    global _openai_stt_disabled

    if STT_ENGINE in ("openai", "google", "local"):
        text = await _run(STT_ENGINE, wav_path, language)
        log.info("%s STT (%d chars): %s", STT_ENGINE, len(text), text[:120])
        return text

    # auto: openai -> google -> local
    errors: list[str] = []

    if not _openai_stt_disabled and OPENAI_API_KEY:
        try:
            text = await _run("openai", wav_path, language)
            log.info("Whisper API STT (%d chars): %s", len(text), text[:120])
            return text
        except RateLimitError as exc:
            if _is_quota_error(exc):
                _openai_stt_disabled = True
                log.warning("OpenAI STT quota exhausted — using fallbacks only")
                errors.append("openai: quota")
            else:
                raise
        except Exception as exc:
            log.warning("OpenAI STT failed: %s", exc)
            errors.append(f"openai: {exc}")

    if _probe_google():
        try:
            text = await _run("google", wav_path, language)
            log.info("Google STT (%d chars): %s", len(text), text[:120])
            return text
        except Exception as exc:
            log.warning("Google STT failed: %s", exc)
            errors.append(f"google: {exc}")

    if _probe_local():
        try:
            text = await _run("local", wav_path, language)
            log.info("Local Whisper STT (%d chars): %s", len(text), text[:120])
            return text
        except Exception as exc:
            log.exception("Local STT failed")
            errors.append(f"local: {exc}")

    hint = (
        "Install STT: pip install faster-whisper SpeechRecognition\n"
        "Or set STT_ENGINE=local in .env (works without OpenAI quota)"
    )
    raise STTQuotaError(f"No STT backend worked ({'; '.join(errors)}). {hint}")
