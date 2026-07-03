import enum
from typing import Any

__all__ = ["SheetRow", "ChallengeMode", "HSRMode"]

SheetRow = list[Any]


class ChallengeMode(str, enum.Enum):
    """Internal identifier for which HSR endgame mode to fetch and write."""

    APOC = "apoc"

    PF = "pf"

    AA = "aa"

    MOC = "moc"


class HSRMode(str, enum.Enum):
    """Honkai: Star Rail Endgame Mode."""

    APOC = "Apocalyptic Shadow 4"

    PF = "Pure Fiction 4"

    MOC = "Memory of Chaos 4"

    AA = "Anomaly Arbitration"

    AA_KING = "Anomaly Arbitration: King"
