"""Listen in voice channels and run voice commands (STT -> AI -> optional TTS)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import discord

from discord_ai.config import (
    CHAT_WHISPER_DELETE_AFTER,
    LLM_TIMEOUT_SECONDS,
    MIN_SPEECH_BYTES,
    STT_ENGINE,
    VOICE_ERROR_COOLDOWN,
    VOICE_POST_ROLL_MS,
    VOICE_REPLY_TEXT,
    VOICE_REPLY_TTS,
    VOICE_UTTERANCE_COOLDOWN,
    VOICE_WAKE_WORDS,
)
from discord_ai.i18n.languages import resolve_language
from discord_ai.i18n.ui import ui_default, ui_for_user
from discord_ai.logging_setup import get_logger
from discord_ai.services.ai import ask_ai
from discord_ai.services.audio_prep import discord_pcm_to_whisper_wav
from discord_ai.services.settings import settings
from discord_ai.services.stt import STTQuotaError, transcribe_wav
from discord_ai.services.stt_filters import is_valid_transcript
from discord_ai.services.voice_connect import HAS_VOICE_RECV, connect_voice_channel
from discord_ai.services.voice_playback import pcm_audio_source
from discord_ai.tts.synthesizer import synthesize

if TYPE_CHECKING:
    from discord_ai.bot.client import AIBot

if HAS_VOICE_RECV:
    from discord.ext import voice_recv

log = get_logger("voice.listen")

SAMPLE_RATE = 48_000
CHANNELS = 2
SAMPLE_WIDTH = 2
DAVE_READY_TIMEOUT = 20.0


def _strip_wake_word(text: str) -> str | None:
    if not VOICE_WAKE_WORDS:
        return text.strip() or None
    lower = text.lower()
    for word in VOICE_WAKE_WORDS:
        w = word.lower()
        if lower.startswith(w):
            rest = text[len(w) :].lstrip(" ,.:;!?-")
            return rest.strip() or None
        if w in lower:
            idx = lower.index(w)
            rest = text[idx + len(w) :].lstrip(" ,.:;!?-")
            return rest.strip() or None
    return None


async def _wait_dave_ready(vc: discord.VoiceClient, timeout: float = DAVE_READY_TIMEOUT) -> bool:
    """Wait for Discord DAVE encryption before receiving voice (reduces corrupted Opus)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        conn = getattr(vc, "_connection", None)
        session = getattr(conn, "dave_session", None) if conn else None
        if session is not None and getattr(session, "ready", False):
            log.debug("DAVE session ready")
            return True
        await asyncio.sleep(0.25)
    log.warning("DAVE not ready after %.0fs — starting listen anyway", timeout)
    return False


if HAS_VOICE_RECV:

    class CommandListenSink(voice_recv.AudioSink):
        """Buffer one user's speech between speaking-start/stop events."""

        def __init__(
            self,
            *,
            target_user_id: int,
            on_utterance: Callable[[bytes], None],
            loop: asyncio.AbstractEventLoop,
            post_roll_ms: int = VOICE_POST_ROLL_MS,
        ) -> None:
            super().__init__()
            self.target_user_id = target_user_id
            self.on_utterance = on_utterance
            self._loop = loop
            self._post_roll_s = max(0.0, post_roll_ms / 1000.0)
            self._buffer = bytearray()
            self._speaking = False
            self._flushing = False

        def wants_opus(self) -> bool:
            return False

        def write(self, user: discord.User | discord.Member | None, data: voice_recv.VoiceData) -> None:
            if not user or user.id != self.target_user_id:
                return
            if not self._speaking and not self._flushing:
                return
            pcm = data.pcm
            if pcm:
                self._buffer.extend(pcm)

        def cleanup(self) -> None:
            self._buffer.clear()
            self._speaking = False
            self._flushing = False

        def _emit_utterance(self, pcm: bytes, member_id: int) -> None:
            if len(pcm) < MIN_SPEECH_BYTES:
                log.debug("Speech too short (%d bytes), ignored", len(pcm))
                return
            log.debug("Utterance ready (user=%s, %d bytes)", member_id, len(pcm))
            self.on_utterance(pcm)

        async def _flush_after_post_roll(self, member_id: int) -> None:
            if self._post_roll_s > 0:
                await asyncio.sleep(self._post_roll_s)
            if self._speaking:
                return
            self._flushing = False
            pcm = bytes(self._buffer)
            self._buffer.clear()
            self._emit_utterance(pcm, member_id)

        @voice_recv.AudioSink.listener()
        def on_voice_member_speaking_start(self, member: discord.Member) -> None:
            if member.id != self.target_user_id:
                return
            self._flushing = False
            self._buffer.clear()
            self._speaking = True
            log.debug("Speaking started (user=%s)", member.id)

        @voice_recv.AudioSink.listener()
        def on_voice_member_speaking_stop(self, member: discord.Member) -> None:
            if member.id != self.target_user_id:
                return
            self._speaking = False
            self._flushing = True
            log.debug("Speaking stopped (user=%s), post-roll %.0fms", member.id, self._post_roll_s * 1000)
            asyncio.run_coroutine_threadsafe(
                self._flush_after_post_roll(member.id),
                self._loop,
            )


@dataclass
class ListenSession:
    guild_id: int
    user_id: int
    text_channel_id: int
    user_lang: str
    reply_in_voice: bool | None
    sink: object = field(default=None)
    last_utterance_at: float = 0.0
    last_error_at: float = 0.0
    last_error_key: str = ""
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class VoiceListenManager:
    def __init__(self, bot: AIBot) -> None:
        self.bot = bot
        self.sessions: dict[int, ListenSession] = {}

    def is_listening(self, guild_id: int) -> bool:
        return guild_id in self.sessions

    async def _notify_channel(
        self,
        session: ListenSession,
        channel: discord.TextChannel,
        key: str,
        *,
        cooldown: int = VOICE_ERROR_COOLDOWN,
        **fmt: str,
    ) -> None:
        now = time.monotonic()
        if session.last_error_key == key and now - session.last_error_at < cooldown:
            return
        session.last_error_at = now
        session.last_error_key = key
        await channel.send(ui_for_user(session.user_lang, key, **fmt))

    def _make_on_utterance(self, session: ListenSession) -> Callable[[bytes], None]:
        def on_utterance(pcm: bytes) -> None:
            asyncio.run_coroutine_threadsafe(
                self._handle_utterance(
                    session.guild_id,
                    session.user_id,
                    session.text_channel_id,
                    pcm,
                    reply_in_voice=session.reply_in_voice,
                ),
                self.bot.loop,
            )

        return on_utterance

    def _begin_listen(self, vc: voice_recv.VoiceRecvClient, session: ListenSession) -> None:
        sink = CommandListenSink(
            target_user_id=session.user_id,
            on_utterance=self._make_on_utterance(session),
            loop=self.bot.loop,
        )
        session.sink = sink

        def after(err: Exception | None) -> None:
            asyncio.run_coroutine_threadsafe(
                self._on_listen_ended(session.guild_id, err),
                self.bot.loop,
            )

        vc.listen(sink, after=after)

    async def _on_listen_ended(self, guild_id: int, err: Exception | None) -> None:
        session = self.sessions.get(guild_id)
        if not session:
            return

        if err is None:
            log.info("Voice listen ended normally (guild=%s)", guild_id)
            return

        log.error("Voice listen crashed (guild=%s): %s", guild_id, err, exc_info=err)

        guild = self.bot.get_guild(guild_id)
        vc = guild.voice_client if guild else None
        if (
            not vc
            or not isinstance(vc, voice_recv.VoiceRecvClient)
            or not vc.is_connected()
            or guild_id not in self.sessions
        ):
            return

        await asyncio.sleep(1.5)
        try:
            if vc.is_listening():
                vc.stop_listening()
            await _wait_dave_ready(vc)
            self._begin_listen(vc, session)
            log.info("Voice listen restarted (guild=%s)", guild_id)
            channel = self.bot.get_channel(session.text_channel_id)
            if isinstance(channel, discord.TextChannel):
                await self._notify_channel(
                    session,
                    channel,
                    "listen_recovered",
                    cooldown=120,
                )
        except Exception:
            log.exception("Could not restart voice listen (guild=%s)", guild_id)

    async def start(
        self,
        interaction: discord.Interaction,
        *,
        reply_in_voice: bool | None = None,
    ) -> str:
        if not HAS_VOICE_RECV:
            raise RuntimeError(
                "Install voice receive from the DAVE-compatible fork:\n"
                "pip install git+https://github.com/rdphillips7/discord-ext-voice-recv.git@main"
            )
        if not interaction.guild:
            raise RuntimeError(ui_default("use_in_server"))

        user_lang = settings.get(interaction.user.id).language
        member = interaction.guild.get_member(interaction.user.id)
        voice_state = (member.voice if member else None) or interaction.user.voice
        if not voice_state or not voice_state.channel:
            raise RuntimeError(ui_for_user(user_lang, "join_vc"))

        channel = voice_state.channel
        if not isinstance(channel, discord.VoiceChannel):
            raise RuntimeError(ui_for_user(user_lang, "join_vc"))

        guild_id = interaction.guild.id
        await self.stop(guild_id)

        vc = await connect_voice_channel(channel)
        assert isinstance(vc, voice_recv.VoiceRecvClient)

        await _wait_dave_ready(vc)

        session = ListenSession(
            guild_id=guild_id,
            user_id=interaction.user.id,
            text_channel_id=interaction.channel_id,  # type: ignore[assignment]
            user_lang=user_lang,
            reply_in_voice=reply_in_voice,
        )
        self.sessions[guild_id] = session
        self._begin_listen(vc, session)

        log.info(
            "Listen started (guild=%s user=%s channel=%s stt=%s — not Ollama)",
            guild_id,
            session.user_id,
            channel.id,
            STT_ENGINE,
        )

        if VOICE_WAKE_WORDS:
            wake = ui_for_user(user_lang, "wake_word_hint", word=VOICE_WAKE_WORDS[0])
        else:
            wake = ui_for_user(user_lang, "wake_hint")

        return ui_for_user(
            user_lang,
            "listen_started",
            channel=channel.name,
            mention=f"<@{session.user_id}>",
            wake=wake,
        )

    async def stop(self, guild_id: int) -> bool:
        session = self.sessions.pop(guild_id, None)
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return session is not None

        vc = guild.voice_client
        if vc and HAS_VOICE_RECV and isinstance(vc, voice_recv.VoiceRecvClient):
            if vc.is_listening():
                vc.stop_listening()
        if session:
            log.info("Listen stopped (guild=%s)", guild_id)
        return session is not None

    async def _whisper_to_chat(
        self,
        session: ListenSession,
        channel: discord.TextChannel,
        *,
        heard: str,
        reply: str,
    ) -> None:
        delete_after = (
            CHAT_WHISPER_DELETE_AFTER if CHAT_WHISPER_DELETE_AFTER > 0 else None
        )
        await channel.send(
            ui_for_user(
                session.user_lang,
                "voice_whisper",
                mention=f"<@{session.user_id}>",
                heard=heard,
                reply=reply,
            ),
            delete_after=delete_after,
        )

    async def _handle_utterance(
        self,
        guild_id: int,
        user_id: int,
        text_channel_id: int,
        pcm: bytes,
        *,
        reply_in_voice: bool | None,
    ) -> None:
        session = self.sessions.get(guild_id)
        if not session or session.user_id != user_id:
            return

        if session.lock.locked():
            log.debug("Utterance ignored (still processing previous)")
            return

        text_channel = self.bot.get_channel(text_channel_id)
        if not isinstance(text_channel, discord.TextChannel):
            return

        async with session.lock:
            now = time.monotonic()
            if now - session.last_utterance_at < VOICE_UTTERANCE_COOLDOWN:
                log.debug("Utterance ignored (cooldown)")
                return

            wav_path = self.bot.temp_dir / f"stt_{guild_id}_{user_id}.wav"
            try:
                wav_path.write_bytes(discord_pcm_to_whisper_wav(pcm))
                raw = await transcribe_wav(wav_path, language=session.user_lang)
            except STTQuotaError:
                log.error("STT quota exhausted (guild=%s)", guild_id)
                await self._notify_channel(
                    session, text_channel, "quota_exhausted", cooldown=300
                )
                return
            except Exception:
                log.exception("STT failed (guild=%s user=%s)", guild_id, user_id)
                await self._notify_channel(session, text_channel, "stt_failed")
                return
            finally:
                wav_path.unlink(missing_ok=True)

            if not raw:
                return

            if not is_valid_transcript(raw):
                log.info("Ignored STT hallucination/noise: %s", raw[:80])
                return

            command = _strip_wake_word(raw)
            if command is None:
                log.debug("Ignored (no wake word): %s", raw[:80])
                return

            stop_phrases = {
                "stop listening",
                "stop listen",
                "stop",
                "quiet",
                "shut up",
                "стоп",
                "остановись",
                "зупини",
            }
            if command.lower() in stop_phrases:
                await self.stop(guild_id)
                await text_channel.send(
                    ui_for_user(session.user_lang, "listen_stopped"),
                    delete_after=CHAT_WHISPER_DELETE_AFTER or None,
                )
                return

            session.last_utterance_at = time.monotonic()
            log.info("Voice command (user=%s): %s", user_id, command[:120])

            try:
                reply = await asyncio.wait_for(
                    ask_ai(text_channel_id, user_id, command),
                    timeout=float(LLM_TIMEOUT_SECONDS) + 15.0,
                )
            except asyncio.TimeoutError:
                log.error("Voice AI timed out (guild=%s user=%s)", guild_id, user_id)
                await self._notify_channel(
                    session, text_channel, "llm_timeout", cooldown=30
                )
                return
            except Exception as exc:
                log.exception("AI failed for voice command")
                await self._notify_channel(
                    session, text_channel, "ai_error", error=str(exc)
                )
                return

            use_tts = VOICE_REPLY_TTS if reply_in_voice is None else reply_in_voice
            if VOICE_REPLY_TEXT:
                await self._whisper_to_chat(
                    session, text_channel, heard=command, reply=reply
                )

            if use_tts:
                guild = self.bot.get_guild(guild_id)
                vc = guild.voice_client if guild else None
                if vc and vc.is_connected():
                    await _play_tts_on_vc(self.bot, vc, user_id, reply)


async def _play_tts_on_vc(
    bot: AIBot,
    voice_client: discord.VoiceClient,
    user_id: int,
    text: str,
) -> None:
    prefs = settings.get(user_id)
    preset = resolve_language(prefs.language)
    audio_file = bot.temp_dir / f"tts_listen_{user_id}.mp3"

    try:
        await synthesize(
            text,
            audio_file,
            engine=prefs.synthesizer,  # type: ignore[arg-type]
            preset=preset,
            edge_voice=prefs.edge_voice(),
        )
        if voice_client.is_playing():
            if hasattr(voice_client, "stop_playing"):
                voice_client.stop_playing()
            else:
                voice_client.stop()
        done = asyncio.Event()

        def after_play(_err: Exception | None) -> None:
            done.set()

        voice_client.play(pcm_audio_source(str(audio_file)), after=lambda e: after_play(e))
        await done.wait()
    except Exception:
        log.exception("TTS playback failed during listen mode")
    finally:
        audio_file.unlink(missing_ok=True)
