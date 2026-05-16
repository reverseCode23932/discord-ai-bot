"""Localized bot UI strings (not AI replies)."""

from __future__ import annotations

import os

from discord_ai.i18n.languages import DEFAULT_LANGUAGE, resolve_language

# Bot-wide default UI language (env), used before per-user prefs apply
BOT_UI_LANGUAGE = os.getenv("BOT_UI_LANGUAGE", os.getenv("DEFAULT_LANGUAGE", DEFAULT_LANGUAGE)).strip().lower()

UI: dict[str, dict[str, str]] = {
    "en": {
        "join_vc": "Join a voice channel first, then run `/listen` again.",
        "listen_started": (
            "Listening in **{channel}** for {mention}.{wake}\n"
            "Use `/stoplisten` or `/leave` to stop."
        ),
        "wake_hint": " Speak when the green ring appears.",
        "wake_word_hint": " Say **{word}** first, then your command.",
        "listen_stopped": "Stopped listening.",
        "not_listening": "Not listening in this server.",
        "left_vc": "Left voice channel.",
        "not_in_vc": "Not in a voice channel.",
        "listen_failed": "Could not start listening: {error}",
        "listen_recovered": "Voice listen recovered after an audio glitch.",
        "stt_failed": "Could not understand that — try again.",
        "quota_exhausted": (
            "Speech recognition failed. Install: `pip install faster-whisper` "
            "and set `STT_ENGINE=local` in `.env` (works without OpenAI)."
        ),
        "heard_reply": "**Heard:** {heard}\n**Reply:** {reply}",
        "ai_error": "AI error: {error}",
        "history_cleared": "History cleared.",
        "use_in_server": "Use this in a server.",
        "voice_deps": "Voice listen needs:\n{items}",
    },
    "ru": {
        "join_vc": "Сначала зайдите в голосовой канал, затем снова `/listen`.",
        "listen_started": (
            "Слушаю в **{channel}** пользователя {mention}.{wake}\n"
            "Остановка: `/stoplisten` или `/leave`."
        ),
        "wake_hint": " Говорите, когда появится зелёный индикатор.",
        "wake_word_hint": " Сначала скажите **{word}**, затем команду.",
        "listen_stopped": "Прослушивание остановлено.",
        "not_listening": "На этом сервере прослушивание не активно.",
        "left_vc": "Вышел из голосового канала.",
        "not_in_vc": "Бот не в голосовом канале.",
        "listen_failed": "Не удалось начать прослушивание: {error}",
        "listen_recovered": "Голосовое прослушивание восстановлено.",
        "stt_failed": "Не разобрал речь — попробуйте ещё раз.",
        "quota_exhausted": (
            "Распознавание речи не работает. Установите: `pip install faster-whisper` "
            "и укажите `STT_ENGINE=local` в `.env` (без OpenAI)."
        ),
        "heard_reply": "**Услышал:** {heard}\n**Ответ:** {reply}",
        "ai_error": "Ошибка AI: {error}",
        "history_cleared": "История очищена.",
        "use_in_server": "Используйте на сервере.",
        "voice_deps": "Для голоса нужно:\n{items}",
    },
    "uk": {
        "join_vc": "Спочатку зайдіть у голосовий канал, потім знову `/listen`.",
        "listen_started": (
            "Слухаю в **{channel}** користувача {mention}.{wake}\n"
            "Зупинка: `/stoplisten` або `/leave`."
        ),
        "wake_hint": " Говоріть, коли з’явиться зелений індикатор.",
        "wake_word_hint": " Спочатку скажіть **{word}**, потім команду.",
        "listen_stopped": "Прослуховування зупинено.",
        "not_listening": "На цьому сервері прослуховування не активне.",
        "left_vc": "Вийшов із голосового каналу.",
        "not_in_vc": "Бот не в голосовому каналі.",
        "listen_failed": "Не вдалося почати прослуховування: {error}",
        "listen_recovered": "Голосове прослуховування відновлено.",
        "stt_failed": "Не розібрав мову — спробуйте ще.",
        "quota_exhausted": (
            "Розпізнавання мови не працює. Встановіть: `pip install faster-whisper` "
            "і вкажіть `STT_ENGINE=local` у `.env` (без OpenAI)."
        ),
        "heard_reply": "**Почув:** {heard}\n**Відповідь:** {reply}",
        "ai_error": "Помилка AI: {error}",
        "history_cleared": "Історію очищено.",
        "use_in_server": "Використовуйте на сервері.",
        "voice_deps": "Для голосу потрібно:\n{items}",
    },
}


def _lang_pack(code: str) -> dict[str, str]:
    key = resolve_language(code).code
    return UI.get(key) or UI["en"]


def ui_text(lang_code: str, key: str, **kwargs: str) -> str:
    template = _lang_pack(lang_code).get(key) or UI["en"].get(key, key)
    if kwargs:
        return template.format(**kwargs)
    return template


def ui_for_user(user_lang: str, key: str, **kwargs: str) -> str:
    return ui_text(user_lang, key, **kwargs)


def ui_default(key: str, **kwargs: str) -> str:
    return ui_text(BOT_UI_LANGUAGE, key, **kwargs)
