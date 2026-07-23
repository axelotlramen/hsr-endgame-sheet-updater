import bisect
import datetime
import json
from pathlib import Path

__all__ = ["VersionResolver"]

VERSION_FILE = Path("version.json")


class VersionResolver:
    """Resolves a date to the HSR version whose range it falls into, per version.json.

    Each entry in version.json maps a version to its start date; a date belongs to the
    version with the latest start date on or before it, so the current version's entry
    is left open-ended and doesn't need updating until the next patch's start date is
    known and added.
    """

    def __init__(self, path: Path = VERSION_FILE) -> None:
        versions: dict[str, str] = json.loads(path.read_text())
        self._entries = sorted(
            (datetime.date.fromisoformat(start), version)
            for version, start in versions.items()
        )

    def resolve(self, date: datetime.date) -> str:
        starts = [start for start, _ in self._entries]
        index = bisect.bisect_right(starts, date) - 1
        if index < 0:
            earliest = self._entries[0][0]
            raise ValueError(
                f"{date} is before the earliest known version ({earliest})"
            )

        return self._entries[index][1]
