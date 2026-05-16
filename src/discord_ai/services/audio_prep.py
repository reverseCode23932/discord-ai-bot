"""Convert Discord voice PCM to WAV suited for Whisper (mono 16 kHz)."""

from __future__ import annotations

import audioop
import io
import wave

# Discord voice_recv: stereo 48 kHz, 16-bit PCM
DISCORD_SAMPLE_RATE = 48_000
DISCORD_CHANNELS = 2
SAMPLE_WIDTH = 2

# Whisper models expect ~16 kHz mono
WHISPER_SAMPLE_RATE = 16_000


def _normalize_pcm(mono: bytes) -> bytes:
    """Boost quiet Discord mic audio so STT hears speech more clearly."""
    rms = audioop.rms(mono, SAMPLE_WIDTH)
    if rms < 80:
        return mono
    target = 2800
    gain = min(4.0, max(1.0, target / rms))
    return audioop.mul(mono, SAMPLE_WIDTH, gain)


def discord_pcm_to_whisper_wav(pcm: bytes) -> bytes:
    """Downmix stereo 48 kHz PCM to mono 16 kHz WAV."""
    if not pcm:
        return b""

    mono = audioop.tomono(pcm, SAMPLE_WIDTH, 0.5, 0.5)
    mono = _normalize_pcm(mono)
    resampled, _ = audioop.ratecv(
        mono,
        SAMPLE_WIDTH,
        1,
        DISCORD_SAMPLE_RATE,
        WHISPER_SAMPLE_RATE,
        None,
    )

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(WHISPER_SAMPLE_RATE)
        wf.writeframes(resampled)
    return buf.getvalue()
