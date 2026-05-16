"""Connect to voice using VoiceRecvClient (send + receive)."""

from __future__ import annotations

import discord
from discord.errors import ConnectionClosed

from discord_ai.logging_setup import get_logger

log = get_logger("voice")

try:
    from discord.ext import voice_recv

    HAS_VOICE_RECV = True
except ImportError:
    voice_recv = None  # type: ignore[assignment]
    HAS_VOICE_RECV = False


async def connect_voice_channel(
    channel: discord.VoiceChannel,
) -> discord.VoiceClient:
    if not HAS_VOICE_RECV:
        raise RuntimeError(
            "discord-ext-voice-recv is not installed. "
            "Run: pip install discord-ext-voice-recv"
        )

    guild = channel.guild
    vc = guild.voice_client

    if vc is not None and not isinstance(vc, voice_recv.VoiceRecvClient):
        log.info("Replacing voice client with VoiceRecvClient")
        await vc.disconnect()
        vc = None

    try:
        if vc is None:
            log.debug("Connecting to voice channel %s", channel.id)
            vc = await channel.connect(cls=voice_recv.VoiceRecvClient)
        elif vc.channel != channel:
            log.debug("Moving voice client to channel %s", channel.id)
            await vc.move_to(channel)
    except ConnectionClosed as exc:
        if getattr(exc, "code", None) == 4017:
            raise RuntimeError(
                "Discord voice error 4017 (DAVE/E2EE). Install: pip install davey"
            ) from exc
        raise

    return vc
