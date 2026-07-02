import typing

import pydantic

import datetime

from models.enums import Element
from models.model import Aliased

class PartialTime(pydantic.BaseModel):
    """Partial time model."""

    year: int
    month: int
    day: int
    hour: int
    minute: int

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime(self.year, self.month, self.day, self.hour, self.minute)
    
class FloorCharacter(pydantic.BaseModel):
    id: int
    level: int
    icon: str
    rarity: int
    element: Element
    eidolon: int = Aliased("rank")

class ChallengeBuff(pydantic.BaseModel):
    id: int
    name: str = Aliased("name_mi18n")
    description: str = Aliased("desc_mi18n")
    icon: str

class ApocalypticShadowBoss(pydantic.BaseModel):
    id: int
    name: str = Aliased("name_mi18n")
    icon: str

class ApocalypticShadowSeason(pydantic.BaseModel):
    id: int = Aliased("schedule_id")
    name: str = Aliased("name_mi18n")
    status: str
    begin_time: PartialTime
    end_time: PartialTime

    upper_boss: typing.Optional[ApocalypticShadowBoss]
    lower_boss: typing.Optional[ApocalypticShadowBoss]
    starward_boss: typing.Optional[ApocalypticShadowBoss] = Aliased("tierce_boss", default=None)

class ApocalypticShadowFloorNode(pydantic.BaseModel):
    challenge_time: typing.Optional[PartialTime]
    avatars: list[FloorCharacter]
    buff: typing.Optional[ChallengeBuff]
    score: int
    boss_defeated: bool

class ApocalypticShadowFloor(pydantic.BaseModel):
    id: int = Aliased("maze_id")
    name: str
    total_stars: int = Aliased("star_num")
    starward_stars: int = Aliased("extra_star_num", default=0)
    is_quick_clear: bool = Aliased("is_fast")
    has_starward_mode: bool = Aliased("is_tierce", default=False)

    last_update_time: PartialTime

    node_1: typing.Optional[ApocalypticShadowFloorNode] = Aliased(default=None)
    node_2: typing.Optional[ApocalypticShadowFloorNode] = Aliased(default=None)
    node_3: typing.Optional[ApocalypticShadowFloorNode] = Aliased(default=None)

class ApocalypticShadow(pydantic.BaseModel):
    """Apocalyptic shadow challenge. """
    total_stars: int = Aliased("star_num")
    starward_stars: int = Aliased("extra_star_num", default=0)
    max_floor: str
    challenge_attempts: int = Aliased("battle_num")
    has_data: bool

    floors: list[ApocalypticShadowFloor] = Aliased("all_floor_detail")
    seasons: list[ApocalypticShadowSeason] = Aliased("groups")