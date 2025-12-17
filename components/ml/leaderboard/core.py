"""Leaderboard business logic."""
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Sequence
from heapq import nlargest

_entries: list["Entry"] = []


@dataclass(slots=True, frozen=False)
class Entry:
    """Leaderboard entry model with slots for performance."""

    user_id: str
    username: str
    score: int
    rank: int | None = None
    created_at: datetime | None = None

    def __lt__(self, other: "LeaderboardEntry") -> bool:
        """Enable sorting by score for heapq."""
        return self.score < other.score


def get_top_entries(limit: int = 10) -> Sequence[Entry]:
    """Get top leaderboard entries using heap for O(n log k) performance."""
    if not _entries:
        return []
    
    if limit >= len(_entries):
        top_entries = sorted(_entries, reverse=True)
    else:
        top_entries = list(reversed(nlargest(limit, _entries)))
    
    for i, entry in enumerate(top_entries, start=1):
        entry.rank = i
    
    return top_entries


def add_entry(entry: Entry) -> None:
    """Add a new leaderboard entry."""
    if entry.created_at is None:
        entry.created_at = datetime.now()
    _entries.append(entry)
