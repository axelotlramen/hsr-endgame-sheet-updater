import pydantic

from .apoc import ApocalypticShadowSeason, FloorCharacter, PartialTime
from .model import Aliased

__all__ = [
    "MemoryOfChaosFloorNode",
    "MemoryOfChaosFloor",
    "MemoryOfChaos",
]


class MemoryOfChaosFloorNode(pydantic.BaseModel):
    challenge_time: PartialTime | None
    avatars: list[FloorCharacter]


class MemoryOfChaosFloor(pydantic.BaseModel):
    id: int = Aliased("maze_id")
    name: str
    cycles_used: int = Aliased("round_num")
    total_stars: int = Aliased("star_num")
    starward_stars: int = Aliased("extra_star_num", default=0)
    is_quick_clear: bool = Aliased("is_fast")
    has_starward_mode: bool = Aliased("is_tierce", default=False)

    node_1: MemoryOfChaosFloorNode | None = Aliased(default=None)
    node_2: MemoryOfChaosFloorNode | None = Aliased(default=None)
    node_3: MemoryOfChaosFloorNode | None = Aliased(default=None)


class MemoryOfChaos(pydantic.BaseModel):
    """Memory of chaos challenge."""

    total_stars: int = Aliased("star_num")
    starward_stars: int = Aliased("extra_star_num", default=0)
    max_floor: str
    challenge_attempts: int = Aliased("battle_num")
    has_data: bool

    floors: list[MemoryOfChaosFloor] = Aliased("all_floor_detail")
    seasons: list[ApocalypticShadowSeason] = Aliased("groups")
