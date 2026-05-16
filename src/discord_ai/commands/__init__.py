from __future__ import annotations

import discord
from discord import app_commands

from discord_ai.bot.client import AIBot
from discord_ai.commands.prefix import register_prefix
from discord_ai.commands.slash import register_slash
from discord_ai.logging_setup import get_logger

log = get_logger("commands")


def register_commands(bot: AIBot) -> None:
    register_slash(bot)
    register_prefix(bot)

    @bot.tree.error
    async def on_tree_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        cmd = interaction.command.name if interaction.command else "unknown"
        user = interaction.user.id if interaction.user else "?"
        log.error(
            "Slash command /%s failed (user=%s channel=%s)",
            cmd,
            user,
            interaction.channel_id,
            exc_info=error,
        )
