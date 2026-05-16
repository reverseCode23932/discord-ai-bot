"""Per-channel chat history for OpenAI context."""

from __future__ import annotations

from collections import defaultdict, deque

from discord_ai.config import MAX_HISTORY
from discord_ai.logging_setup import get_logger

log = get_logger("history")


class HistoryStore:
    def __init__(self) -> None:
        self._store: dict[int, deque[dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=MAX_HISTORY)
        )

    def get(self, channel_id: int) -> list[dict[str, str]]:
        return list(self._store[channel_id])

    def add(self, channel_id: int, role: str, content: str) -> None:
        self._store[channel_id].append({"role": role, "content": content})
        log.debug(
            "History add (channel=%s role=%s size=%d)",
            channel_id,
            role,
            len(self._store[channel_id]),
        )

    def clear(self, channel_id: int) -> None:
        had = channel_id in self._store
        self._store.pop(channel_id, None)
        if had:
            log.info("History cleared (channel=%s)", channel_id)


history = HistoryStore()
