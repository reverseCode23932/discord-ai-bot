"""Voice dependency checks (PyNaCl + davey for Discord DAVE/E2EE voice)."""

from __future__ import annotations

from discord_ai.config import STT_ENGINE
from discord_ai.logging_setup import get_logger
from discord_ai.services.stt import _probe_google, _probe_local

log = get_logger("voice")


def check_voice_dependencies() -> list[str]:
    """Return human-readable missing dependency messages."""
    missing: list[str] = []

    try:
        import nacl  # noqa: F401
    except ImportError:
        missing.append("PyNaCl — pip install PyNaCl")

    try:
        import davey  # noqa: F401
    except ImportError:
        missing.append(
            "davey — pip install davey  (required since Discord enforced DAVE voice encryption)"
        )

    try:
        from discord.ext import voice_recv  # noqa: F401
    except ImportError:
        missing.append(
            "discord-ext-voice-recv — pip install -r requirements.txt  (DAVE fork, for /listen)"
        )
    else:
        try:
            import inspect
            from discord.ext.voice_recv import opus

            if "dave_session.decrypt" not in inspect.getsource(opus.PacketDecoder._process_packet):
                missing.append(
                    "discord-ext-voice-recv (old build) — pip install -r requirements.txt for DAVE fix"
                )
        except Exception:
            pass

    if STT_ENGINE in ("google", "auto", "hybrid") and not _probe_google():
        missing.append("SpeechRecognition — pip install SpeechRecognition  (Google STT)")

    if STT_ENGINE in ("local", "auto", "hybrid") and not _probe_local():
        missing.append("faster-whisper — pip install faster-whisper  (local STT, no API)")

    return missing


def log_voice_dependency_status() -> bool:
    missing = check_voice_dependencies()
    if missing:
        log.warning(
            "Voice/TTS will fail until installed: %s",
            "; ".join(missing),
        )
        return False
    log.info("Voice dependencies OK (PyNaCl + davey)")
    return True
