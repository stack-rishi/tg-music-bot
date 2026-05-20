import random
import os
from enum import Enum
from typing import Optional


class LoopMode(Enum):
    OFF = "off"
    SINGLE = "single"
    ALL = "all"


def _cleanup_track_file(track: Optional[dict]) -> None:
    """Helper to delete local files associated with a track."""
    if not track:
        return
    if track.get("local_file") and track.get("stream_url"):
        try:
            path = track["stream_url"]
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


class _ChatQueue:
    """Queue state for a single chat."""

    __slots__ = ("current", "upcoming", "loop_mode")

    def __init__(self) -> None:
        self.current: Optional[dict] = None
        self.upcoming: list[dict] = []
        self.loop_mode: LoopMode = LoopMode.OFF

    def add(self, track: dict) -> int:
        """Add a track; returns its 1-based position in the upcoming list."""
        self.upcoming.append(track)
        return len(self.upcoming)

    def advance(self) -> Optional[dict]:
        """Move to the next track based on loop mode.

        Returns the next track or None if queue is exhausted.
        """
        if self.loop_mode == LoopMode.SINGLE and self.current:
            return self.current

        if self.loop_mode == LoopMode.ALL and self.current:
            self.upcoming.append(self.current)

        if self.upcoming:
            self.current = self.upcoming.pop(0)
            return self.current

        self.current = None
        return None

    def skip(self) -> Optional[dict]:
        """Force-skip current track (ignores SINGLE loop).

        Returns the next track or None.
        """
        old_current = self.current
        if self.loop_mode == LoopMode.ALL and old_current:
            self.upcoming.append(old_current)
        else:
            _cleanup_track_file(old_current)

        if self.upcoming:
            self.current = self.upcoming.pop(0)
            return self.current

        self.current = None
        return None

    def shuffle(self) -> None:
        """Shuffle the upcoming tracks (current stays)."""
        random.shuffle(self.upcoming)

    def clear(self) -> None:
        """Clear upcoming tracks; current still plays."""
        for track in self.upcoming:
            _cleanup_track_file(track)
        self.upcoming.clear()

    def full_clear(self) -> None:
        """Clear everything including the current track."""
        _cleanup_track_file(self.current)
        for track in self.upcoming:
            _cleanup_track_file(track)
        self.current = None
        self.upcoming.clear()

    def toggle_loop(self) -> LoopMode:
        """Cycle loop mode: OFF → SINGLE → ALL → OFF."""
        cycle = [LoopMode.OFF, LoopMode.SINGLE, LoopMode.ALL]
        idx = (cycle.index(self.loop_mode) + 1) % len(cycle)
        self.loop_mode = cycle[idx]
        return self.loop_mode


class QueueManager:
    """Manages per-chat queues."""

    def __init__(self) -> None:
        self._queues: dict[int, _ChatQueue] = {}

    def _get(self, chat_id: int) -> _ChatQueue:
        if chat_id not in self._queues:
            self._queues[chat_id] = _ChatQueue()
        return self._queues[chat_id]

    def add(self, chat_id: int, track: dict) -> int:
        """Add track to chat queue. Returns position."""
        return self._get(chat_id).add(track)

    def get_current(self, chat_id: int) -> Optional[dict]:
        return self._get(chat_id).current

    def set_current(self, chat_id: int, track: dict) -> None:
        self._get(chat_id).current = track

    def advance(self, chat_id: int) -> Optional[dict]:
        return self._get(chat_id).advance()

    def skip(self, chat_id: int) -> Optional[dict]:
        return self._get(chat_id).skip()

    def shuffle(self, chat_id: int) -> None:
        self._get(chat_id).shuffle()

    def clear(self, chat_id: int) -> None:
        """Clear upcoming queue only."""
        self._get(chat_id).clear()

    def full_clear(self, chat_id: int) -> None:
        """Clear everything and remove chat state."""
        if chat_id in self._queues:
            self._queues[chat_id].full_clear()
            del self._queues[chat_id]

    def toggle_loop(self, chat_id: int) -> LoopMode:
        return self._get(chat_id).toggle_loop()

    def get_loop_mode(self, chat_id: int) -> str:
        return self._get(chat_id).loop_mode.value

    def get_queue(self, chat_id: int) -> list[dict]:
        return list(self._get(chat_id).upcoming)

    def get_length(self, chat_id: int) -> int:
        return len(self._get(chat_id).upcoming)

    def is_empty(self, chat_id: int) -> bool:
        q = self._get(chat_id)
        return q.current is None and not q.upcoming
