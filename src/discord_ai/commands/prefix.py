"""Prefix commands (!ask, !lang, ...)."""

from __future__ import annotations

from discord.ext import commands

from discord_ai.bot.client import AIBot
from discord_ai.i18n.languages import resolve_language
from discord_ai.services.ai import ask_ai
from discord_ai.services.history import history
from discord_ai.services.settings import format_prefs, settings
from discord_ai.logging_setup import get_logger

log = get_logger("commands.prefix")


def register_prefix(bot: AIBot) -> None:
    @bot.command(name="lang")
    async def prefix_lang(ctx: commands.Context, code: str | None = None) -> None:
        if code is None:
            prefs = settings.get(ctx.author.id)
            await ctx.reply(format_prefs(prefs))
            return
        try:
            prefs = settings.update(ctx.author.id, language=code)
            lang = resolve_language(prefs.language)
            await ctx.reply(f"Language: {lang.name} (`{lang.code}`)")
        except ValueError as exc:
            await ctx.reply(str(exc))

    @bot.command(name="ask")
    async def prefix_ask(ctx: commands.Context, *, question: str) -> None:
        log.info(
            "!ask (user=%s channel=%s prompt_len=%d)",
            ctx.author.id,
            ctx.channel.id,
            len(question),
        )
        async with ctx.typing():
            try:
                reply = await ask_ai(ctx.channel.id, ctx.author.id, question)
            except Exception as exc:
                await ctx.reply(f"AI error: {exc}")
                return
        await ctx.reply(reply)

    @bot.command(name="reset")
    async def prefix_reset(ctx: commands.Context) -> None:
        history.clear(ctx.channel.id)
        await ctx.reply("History cleared.")
