"""Language presets: AI reply language + default TTS voices."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguagePreset:
    code: str
    name: str
    prompt: str
    edge_voice: str
    gtts_lang: str
    voices: tuple[str, ...]


LANGUAGE_PRESETS: dict[str, LanguagePreset] = {
    "en": LanguagePreset(
        code="en",
        name="English",
        prompt="Always reply in English.",
        edge_voice="en-US-AriaNeural",
        gtts_lang="en",
        voices=(
            "en-US-AriaNeural",
            "en-US-GuyNeural",
            "en-GB-SoniaNeural",
            "en-GB-RyanNeural",
        ),
    ),
    "ru": LanguagePreset(
        code="ru",
        name="Русский",
        prompt="Всегда отвечай на русском языке. Говори коротко и ясно.",
        edge_voice="ru-RU-DmitryNeural",
        gtts_lang="ru",
        voices=(
            "ru-RU-DmitryNeural",
            "ru-RU-SvetlanaNeural",
        ),
    ),
    "uk": LanguagePreset(
        code="uk",
        name="Українська",
        prompt="Завжди відповідай українською мовою.",
        edge_voice="uk-UA-PolinaNeural",
        gtts_lang="uk",
        voices=("uk-UA-PolinaNeural", "uk-UA-OstapNeural"),
    ),
    "de": LanguagePreset(
        code="de",
        name="Deutsch",
        prompt="Antworte immer auf Deutsch.",
        edge_voice="de-DE-KatjaNeural",
        gtts_lang="de",
        voices=("de-DE-KatjaNeural", "de-DE-ConradNeural"),
    ),
    "fr": LanguagePreset(
        code="fr",
        name="Français",
        prompt="Réponds toujours en français.",
        edge_voice="fr-FR-DeniseNeural",
        gtts_lang="fr",
        voices=("fr-FR-DeniseNeural", "fr-FR-HenriNeural"),
    ),
    "es": LanguagePreset(
        code="es",
        name="Español",
        prompt="Responde siempre en español.",
        edge_voice="es-ES-ElviraNeural",
        gtts_lang="es",
        voices=("es-ES-ElviraNeural", "es-ES-AlvaroNeural"),
    ),
    "pt": LanguagePreset(
        code="pt",
        name="Português",
        prompt="Responda sempre em português.",
        edge_voice="pt-BR-FranciscaNeural",
        gtts_lang="pt",
        voices=("pt-BR-FranciscaNeural", "pt-BR-AntonioNeural"),
    ),
    "ja": LanguagePreset(
        code="ja",
        name="日本語",
        prompt="常に日本語で返答してください。",
        edge_voice="ja-JP-NanamiNeural",
        gtts_lang="ja",
        voices=("ja-JP-NanamiNeural", "ja-JP-KeitaNeural"),
    ),
    "zh": LanguagePreset(
        code="zh",
        name="中文",
        prompt="请始终使用简体中文回复。",
        edge_voice="zh-CN-XiaoxiaoNeural",
        gtts_lang="zh-cn",
        voices=("zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"),
    ),
    "pl": LanguagePreset(
        code="pl",
        name="Polski",
        prompt="Zawsze odpowiadaj po polsku.",
        edge_voice="pl-PL-ZofiaNeural",
        gtts_lang="pl",
        voices=("pl-PL-ZofiaNeural", "pl-PL-MarekNeural"),
    ),
    "tr": LanguagePreset(
        code="tr",
        name="Türkçe",
        prompt="Her zaman Türkçe yanıt ver.",
        edge_voice="tr-TR-EmelNeural",
        gtts_lang="tr",
        voices=("tr-TR-EmelNeural", "tr-TR-AhmetNeural"),
    ),
}

DEFAULT_LANGUAGE = "en"
SYNTHESIZER_CHOICES = ("edge", "gtts")


def resolve_language(code: str | None) -> LanguagePreset:
    key = (code or DEFAULT_LANGUAGE).strip().lower()
    if key in LANGUAGE_PRESETS:
        return LANGUAGE_PRESETS[key]
    raise ValueError(
        f"Unknown language `{key}`. "
        f"Available: {', '.join(sorted(LANGUAGE_PRESETS))}"
    )


def language_list_text() -> str:
    return "\n".join(f"`{p.code}` — {p.name}" for p in LANGUAGE_PRESETS.values())
