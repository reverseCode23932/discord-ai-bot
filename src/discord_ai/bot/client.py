"""Discord bot client and event handlers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import discord
from discord.ext import commands

from discord_ai.config import BOT_PREFIX
from discord_ai.logging_setup import get_logger
from discord_ai.services.ai import ask_ai
from discord_ai.services.voice_listen import VoiceListenManager

log = get_logger("bot")


class AIBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        self.temp_dir = Path(tempfile.gettempdir()) / "discord-ai-bot"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.listen_manager = VoiceListenManager(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()
        log.info("Slash commands synced (user=%s)", self.user)

    async def on_ready(self) -> None:
        log.info("Bot ready: %s (id=%s)", self.user, self.user.id if self.user else "?")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        log.error(
            "Prefix command error: %s (user=%s channel=%s)",
            ctx.command,
            ctx.author.id,
            ctx.channel.id,
            exc_info=error,
        )

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.content:
            return

        mentioned = self.user and self.user in message.mentions
        prefixed = message.content.startswith(BOT_PREFIX)
        if not mentioned and not prefixed:
            return

        prompt = message.content
        if prefixed:
            prompt = prompt[len(BOT_PREFIX) :].strip()
        if self.user:
            prompt = prompt.replace(f"<@{self.user.id}>", "").strip()
        if not prompt:
            await message.channel.send(
                "Ask me something after mentioning me or using the prefix."
            )
            return

        log.info(
            "Message prompt (user=%s channel=%s len=%d)",
            message.author.id,
            message.channel.id,
            len(prompt),
        )
        log.debug("Prompt text: %s", prompt[:500])

        async with message.channel.typing():
            try:
                reply = await ask_ai(message.channel.id, message.author.id, prompt)
            except Exception as exc:
                log.exception(
                    "AI failed for message (user=%s channel=%s)",
                    message.author.id,
                    message.channel.id,
                )
                await message.reply(f"AI error: {exc}")
                return

        await message.reply(reply)
