"""Per-user language and TTS preferences."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from discord_ai.config import DATA_DIR, DEFAULT_EDGE_VOICE
from discord_ai.i18n.languages import (
    DEFAULT_LANGUAGE,
    SYNTHESIZER_CHOICES,
    resolve_language,
)
from discord_ai.logging_setup import get_logger

log = get_logger("settings")

SETTINGS_FILE = DATA_DIR / "user_settings.json"

DEFAULT_SYNTHESIZER = os.getenv("DEFAULT_SYNTHESIZER", "edge").strip().lower()
if DEFAULT_SYNTHESIZER not in SYNTHESIZER_CHOICES:
    DEFAULT_SYNTHESIZER = "edge"

DEFAULT_LANG_CODE = os.getenv("DEFAULT_LANGUAGE", DEFAULT_LANGUAGE).strip().lower()
try:
    resolve_language(DEFAULT_LANG_CODE)
except ValueError:
    DEFAULT_LANG_CODE = DEFAULT_LANGUAGE


@dataclass
class UserPrefs:
    language: str = DEFAULT_LANG_CODE
    synthesizer: str = DEFAULT_SYNTHESIZER
    voice: str | None = None

    def edge_voice(self) -> str:
        if self.voice:
            return self.voice
        if DEFAULT_EDGE_VOICE:
            return DEFAULT_EDGE_VOICE
        preset = resolve_language(self.language)
        return preset.edge_voice


class SettingsStore:
    def __init__(self, path: Path = SETTINGS_FILE) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, UserPrefs] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            log.info("No settings file yet: %s", self.path)
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Could not load settings from %s: %s", self.path, exc)
            return
        for user_id, data in raw.items():
            if isinstance(data, dict):
                self._cache[user_id] = UserPrefs(
                    language=str(data.get("language", DEFAULT_LANG_CODE)),
                    synthesizer=str(data.get("synthesizer", DEFAULT_SYNTHESIZER)),
                    voice=data.get("voice"),
                )
        log.info("Loaded settings for %d user(s) from %s", len(self._cache), self.path)

    def _save(self) -> None:
        payload = {uid: asdict(prefs) for uid, prefs in self._cache.items()}
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.debug("Saved settings (%d users)", len(self._cache))

    def get(self, user_id: int) -> UserPrefs:
        key = str(user_id)
        if key not in self._cache:
            self._cache[key] = UserPrefs()
            log.debug("New user prefs (user=%s)", user_id)
        return self._cache[key]

    def update(self, user_id: int, **kwargs: object) -> UserPrefs:
        prefs = self.get(user_id)
        if "language" in kwargs and kwargs["language"] is not None:
            resolve_language(str(kwargs["language"]))
            prefs.language = str(kwargs["language"]).lower()
        if "synthesizer" in kwargs and kwargs["synthesizer"] is not None:
            synth = str(kwargs["synthesizer"]).lower()
            if synth not in SYNTHESIZER_CHOICES:
                raise ValueError(
                    f"Synthesizer must be one of: {', '.join(SYNTHESIZER_CHOICES)}"
                )
            prefs.synthesizer = synth
        if "voice" in kwargs:
            voice = kwargs["voice"]
            prefs.voice = str(voice) if voice else None
        self._save()
        log.info(
            "Settings updated (user=%s lang=%s synth=%s voice=%s)",
            user_id,
            prefs.language,
            prefs.synthesizer,
            prefs.voice,
        )
        return prefs


def format_prefs(prefs: UserPrefs) -> str:
    lang = resolve_language(prefs.language)
    return (
        f"**Language:** `{lang.code}` ({lang.name})\n"
        f"**Synthesizer:** `{prefs.synthesizer}` "
        f"(`edge` = neural, `gtts` = Google)\n"
        f"**Voice (edge):** `{prefs.edge_voice()}`"
    )


settings = SettingsStore()
