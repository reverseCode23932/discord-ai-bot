"""Voice channel TTS playback."""

from __future__ import annotations

import asyncio
from pathlib import Path

import discord
from discord.errors import ConnectionClosed

from discord_ai.i18n.languages import resolve_language
from discord_ai.logging_setup import get_logger
from discord_ai.services.settings import settings
from discord_ai.services.voice_connect import connect_voice_channel
from discord_ai.services.voice_playback import pcm_audio_source
from discord_ai.services.voice_deps import check_voice_dependencies
from discord_ai.tts.synthesizer import synthesize

log = get_logger("voice")


async def play_tts_in_voice(
    bot: discord.Client,
    temp_dir: Path,
    interaction: discord.Interaction,
    text: str,
    *,
    already_deferred: bool = False,
) -> None:
    user_id = interaction.user.id
    guild_id = interaction.guild.id if interaction.guild else None

    if not interaction.guild or not interaction.user.voice:
        log.warning("TTS skipped: user %s not in voice", user_id)
        msg = "Join a voice channel first."
        if already_deferred:
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return

    channel = interaction.user.voice.channel
    if not isinstance(channel, discord.VoiceChannel):
        log.warning("TTS skipped: invalid voice channel for user %s", user_id)
        msg = "Could not find your voice channel."
        if already_deferred:
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return

    prefs = settings.get(user_id)
    log.info(
        "TTS start (user=%s guild=%s channel=%s engine=%s voice=%s text_len=%d)",
        user_id,
        guild_id,
        channel.id,
        prefs.synthesizer,
        prefs.edge_voice(),
        len(text),
    )

    missing = check_voice_dependencies()
    if missing:
        msg = (
            "Voice is not configured on this machine. Install:\n"
            + "\n".join(f"- {m}" for m in missing)
            + "\n\nThen restart the bot."
        )
        if already_deferred:
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return

    if not already_deferred:
        await interaction.response.defer(thinking=True)

    try:
        voice_client = await connect_voice_channel(channel)
    except ConnectionClosed as exc:
        if getattr(exc, "code", None) == 4017:
            log.error("Voice 4017: DAVE/E2EE required — install davey")
            await interaction.followup.send(
                "Cannot join voice: Discord requires **davey** for encrypted voice.\n"
                "Run: `pip install -U \"discord.py[voice]\" davey PyNaCl` then restart.",
                ephemeral=True,
            )
            return
        raise
    except RuntimeError as exc:
        await interaction.followup.send(str(exc), ephemeral=True)
        return

    preset = resolve_language(prefs.language)
    audio_file = temp_dir / f"tts_{interaction.id}.mp3"

    try:
        await synthesize(
            text,
            audio_file,
            engine=prefs.synthesizer,  # type: ignore[arg-type]
            preset=preset,
            edge_voice=prefs.edge_voice(),
        )
        log.debug("TTS audio saved: %s (%d bytes)", audio_file, audio_file.stat().st_size)

        if voice_client.is_playing():
            if hasattr(voice_client, "stop_playing"):
                voice_client.stop_playing()
            else:
                voice_client.stop()
        source = pcm_audio_source(str(audio_file))
        done = asyncio.Event()

        def after_play(err: Exception | None) -> None:
            if err:
                log.error("Playback error (user=%s): %s", user_id, err)
            done.set()

        voice_client.play(source, after=lambda e: after_play(e))
        await done.wait()
        log.info("TTS finished (user=%s guild=%s)", user_id, guild_id)
        await interaction.followup.send(
            f"Spoke with **{prefs.synthesizer}** ({prefs.edge_voice()})."
        )
    except Exception:
        log.exception("TTS failed (user=%s guild=%s)", user_id, guild_id)
        await interaction.followup.send("TTS error — check logs for details.")
    finally:
        audio_file.unlink(missing_ok=True)
