import enum
from typing import Any

SheetRow = list[Any]


class HSRMode(str, enum.Enum):
    """Honkai: Star Rail Endgame Mode."""

    APOC = "Apocalyptic Shadow 4"

    PF = "Pure Fiction 4"

    MOC = "Memory of Chaos 4"

    AA = "Anomaly Arbitration"

    AA_KING = "Anomaly Arbitration: King"
