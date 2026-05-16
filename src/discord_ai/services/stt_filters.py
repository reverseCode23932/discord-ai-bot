"""Filter common Whisper false positives (silence / noise)."""

from __future__ import annotations

# Substrings often hallucinated on silence (RU/EN)
_HALLUCINATION_MARKERS: tuple[str, ...] = (
    "редактор субтитров",
    "субтитров а.",
    "динамическая музыка",
    "динамичная музыка",
    "subtitle editor",
    "subtitles by",
    "thanks for watching",
    "thank you for watching",
    "please subscribe",
    "подписывайтесь",
    "продолжение следует",
    "to be continued",
    "applause",
    "аплодисменты",
    "[music]",
    "[музыка]",
    "www.",
    "http",
)


def is_valid_transcript(text: str) -> bool:
    cleaned = text.strip()
    if len(cleaned) < 2:
        return False

    lower = cleaned.lower()
    for marker in _HALLUCINATION_MARKERS:
        if marker in lower:
            return False

    # Need at least one letter or digit
    if not any(ch.isalnum() for ch in cleaned):
        return False

    return True
