"""Slash (/) commands."""

from __future__ import annotations

import discord
from discord import app_commands

from discord_ai.bot.client import AIBot
from discord_ai.i18n.languages import language_list_text, resolve_language
from discord_ai.services.ai import ask_ai
from discord_ai.services.history import history
from discord_ai.i18n.ui import ui_for_user
from discord_ai.services.settings import format_prefs, settings
from discord_ai.services.voice import play_tts_in_voice
from discord_ai.services.voice_deps import check_voice_dependencies
from discord_ai.logging_setup import get_logger

log = get_logger("commands.slash")


def _log_invocation(interaction: discord.Interaction, command: str, **fields: object) -> None:
    extra = " ".join(f"{k}={v}" for k, v in fields.items())
    log.info(
        "/%s (user=%s channel=%s%s%s)",
        command,
        interaction.user.id,
        interaction.channel_id,
        " " if extra else "",
        extra,
    )


def register_slash(bot: AIBot) -> None:
    @bot.tree.command(name="ask", description="Ask the AI (uses your language setting)")
    @app_commands.describe(question="Your question")
    async def slash_ask(interaction: discord.Interaction, question: str) -> None:
        _log_invocation(interaction, "ask", prompt_len=len(question))
        await interaction.response.defer(thinking=True)
        try:
            reply = await ask_ai(interaction.channel_id, interaction.user.id, question)
        except Exception as exc:
            await interaction.followup.send(f"AI error: {exc}")
            return
        await interaction.followup.send(reply)

    @bot.tree.command(
        name="say", description="Speak text in voice (your language + synthesizer)"
    )
    @app_commands.describe(text="Text to speak")
    async def slash_say(interaction: discord.Interaction, text: str) -> None:
        _log_invocation(interaction, "say", text_len=len(text))
        await play_tts_in_voice(bot, bot.temp_dir, interaction, text)

    @bot.tree.command(
        name="askvoice", description="Ask AI and speak the answer in voice"
    )
    @app_commands.describe(question="Your question")
    async def slash_askvoice(interaction: discord.Interaction, question: str) -> None:
        _log_invocation(interaction, "askvoice", prompt_len=len(question))
        await interaction.response.defer(thinking=True)
        try:
            reply = await ask_ai(interaction.channel_id, interaction.user.id, question)
        except Exception as exc:
            await interaction.followup.send(f"AI error: {exc}")
            return
        await interaction.followup.send(reply)
        await play_tts_in_voice(
            bot, bot.temp_dir, interaction, reply, already_deferred=True
        )

    @bot.tree.command(
        name="language",
        description="Set or view reply/TTS language (en, ru, de, uk, ...)",
    )
    @app_commands.describe(code="Language code, e.g. en or ru")
    async def slash_language(
        interaction: discord.Interaction, code: str | None = None
    ) -> None:
        _log_invocation(interaction, "language", code=code or "list")
        if code is None:
            prefs = settings.get(interaction.user.id)
            await interaction.response.send_message(
                f"Your settings:\n{format_prefs(prefs)}\n\n"
                f"**Available languages:**\n{language_list_text()}",
                ephemeral=True,
            )
            return
        try:
            prefs = settings.update(interaction.user.id, language=code)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        lang = resolve_language(prefs.language)
        await interaction.response.send_message(
            f"Language set to **{lang.name}** (`{lang.code}`).\n"
            f"Default voice: `{lang.edge_voice}`",
            ephemeral=True,
        )

    @bot.tree.command(
        name="synthesizer",
        description="Choose TTS engine: edge (neural) or gtts (Google)",
    )
    @app_commands.describe(engine="edge or gtts")
    @app_commands.choices(
        engine=[
            app_commands.Choice(
                name="edge — Microsoft neural (best quality)", value="edge"
            ),
            app_commands.Choice(name="gtts — Google TTS (simpler)", value="gtts"),
        ]
    )
    async def slash_synthesizer(
        interaction: discord.Interaction,
        engine: app_commands.Choice[str],
    ) -> None:
        try:
            prefs = settings.update(interaction.user.id, synthesizer=engine.value)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.send_message(
            f"Synthesizer set to `{prefs.synthesizer}`.", ephemeral=True
        )

    @bot.tree.command(
        name="voice",
        description="Set Edge TTS voice (only when synthesizer is edge)",
    )
    @app_commands.describe(name="Voice id, e.g. ru-RU-SvetlanaNeural")
    async def slash_voice(
        interaction: discord.Interaction, name: str | None = None
    ) -> None:
        prefs = settings.get(interaction.user.id)
        preset = resolve_language(prefs.language)

        if name is None:
            voices = "\n".join(f"`{v}`" for v in preset.voices)
            await interaction.response.send_message(
                f"Current voice: `{prefs.edge_voice()}`\n\n"
                f"**Voices for {preset.name}:**\n{voices}\n\n"
                "Use `/voice name:...` to change.",
                ephemeral=True,
            )
            return

        settings.update(interaction.user.id, voice=name)
        await interaction.response.send_message(f"Voice set to `{name}`.", ephemeral=True)

    @bot.tree.command(name="settings", description="Show language and TTS settings")
    async def slash_settings(interaction: discord.Interaction) -> None:
        prefs = settings.get(interaction.user.id)
        await interaction.response.send_message(format_prefs(prefs), ephemeral=True)

    @bot.tree.command(name="reset", description="Clear conversation history")
    async def slash_reset(interaction: discord.Interaction) -> None:
        history.clear(interaction.channel_id)
        await interaction.response.send_message("History cleared.", ephemeral=True)

    @bot.tree.command(
        name="listen",
        description="Join your voice channel and listen for your spoken commands",
    )
    @app_commands.describe(
        reply_in_voice="Speak the AI reply in voice (default: on)",
    )
    async def slash_listen(
        interaction: discord.Interaction,
        reply_in_voice: bool = True,
    ) -> None:
        _log_invocation(interaction, "listen")
        lang = settings.get(interaction.user.id).language
        missing = check_voice_dependencies()
        if missing:
            await interaction.response.send_message(
                ui_for_user(
                    lang,
                    "voice_deps",
                    items="\n".join(f"- {m}" for m in missing),
                ),
                ephemeral=True,
            )
            return
        await interaction.response.defer(thinking=True)
        try:
            msg = await bot.listen_manager.start(
                interaction, reply_in_voice=reply_in_voice
            )
        except Exception as exc:
            log.exception("Failed to start listening")
            await interaction.followup.send(
                ui_for_user(lang, "listen_failed", error=str(exc)),
                ephemeral=True,
            )
            return
        await interaction.followup.send(msg, ephemeral=True)

    @bot.tree.command(name="stoplisten", description="Stop listening for voice commands")
    async def slash_stoplisten(interaction: discord.Interaction) -> None:
        _log_invocation(interaction, "stoplisten")
        lang = settings.get(interaction.user.id).language
        if not interaction.guild:
            await interaction.response.send_message(
                ui_for_user(lang, "use_in_server"), ephemeral=True
            )
            return
        stopped = await bot.listen_manager.stop(interaction.guild.id)
        if stopped:
            await interaction.response.send_message(
                ui_for_user(lang, "listen_stopped"), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                ui_for_user(lang, "not_listening"), ephemeral=True
            )

    @bot.tree.command(name="leave", description="Leave voice and stop listening")
    async def slash_leave(interaction: discord.Interaction) -> None:
        lang = settings.get(interaction.user.id).language
        if interaction.guild:
            await bot.listen_manager.stop(interaction.guild.id)
        if interaction.guild and interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message(
                ui_for_user(lang, "left_vc"), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                ui_for_user(lang, "not_in_vc"), ephemeral=True
            )
