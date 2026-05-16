"""Discord voice playback helpers (FFmpeg filters for clearer TTS)."""

from __future__ import annotations

import discord

from discord_ai.config import FFMPEG_PCM_OPTIONS


def pcm_audio_source(path: str) -> discord.FFmpegPCMAudio:
    """Play TTS in voice with light EQ/normalization for Discord."""
    return discord.FFmpegPCMAudio(path, options=FFMPEG_PCM_OPTIONS)
