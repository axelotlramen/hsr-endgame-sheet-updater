import pydantic

from .apoc import ChallengeBuff, FloorCharacter, PartialTime
from .model import Aliased

__all__ = [
    "PureFictionSeason",
    "PureFictionFloorNode",
    "PureFictionFloor",
    "PureFiction",
]


class PureFictionSeason(pydantic.BaseModel):
    id: int = Aliased("schedule_id")
    name: str = Aliased("name_mi18n")
    status: str
    begin_time: PartialTime
    end_time: PartialTime


class PureFictionFloorNode(pydantic.BaseModel):
    challenge_time: PartialTime | None
    avatars: list[FloorCharacter]
    buff: ChallengeBuff | None
    score: int


class PureFictionFloor(pydantic.BaseModel):
    id: int = Aliased("maze_id")
    name: str
    round_num: int
    total_stars: int = Aliased("star_num")
    starward_stars: int = Aliased("extra_star_num", default=0)
    is_quick_clear: bool = Aliased("is_fast")
    has_starward_mode: bool = Aliased("is_tierce", default=False)

    node_1: PureFictionFloorNode | None = Aliased(default=None)
    node_2: PureFictionFloorNode | None = Aliased(default=None)
    node_3: PureFictionFloorNode | None = Aliased(default=None)

    @property
    def score(self) -> int:
        """Total score of the floor."""
        return sum(
            node.score
            for node in (self.node_1, self.node_2, self.node_3)
            if node is not None
        )


class PureFiction(pydantic.BaseModel):
    """Pure fiction challenge."""

    total_stars: int = Aliased("star_num")
    starward_stars: int = Aliased("extra_star_num", default=0)
    max_floor: str
    challenge_attempts: int = Aliased("battle_num")
    has_data: bool

    floors: list[PureFictionFloor] = Aliased("all_floor_detail")
    seasons: list[PureFictionSeason] = Aliased("groups")
