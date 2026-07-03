import pydantic

from .apoc import ChallengeBuff, FloorCharacter, PartialTime
from .model import Aliased

__all__ = [
    "AnomalySeason",
    "AnomalyBossInfo",
    "AnomalyMiniBossInfo",
    "AnomalyBossRecord",
    "AnomalyMiniBossRecord",
    "AnomalyRecord",
    "AnomalySummary",
    "AnomalyPlayer",
    "AnomalyArbitration",
]


class AnomalySeason(pydantic.BaseModel):
    id: int = Aliased("group_id")
    name: str = Aliased("name_mi18n")
    status: str
    begin_time: PartialTime
    end_time: PartialTime
    game_version: str
    icon: str = Aliased("theme_pic_path")


class AnomalyBossInfo(pydantic.BaseModel):
    id: int = Aliased("maze_id")
    name: str = Aliased("name_mi18n")
    game_mode_name: str = Aliased("hard_mode_name_mi18n")
    icon: str


class AnomalyMiniBossInfo(pydantic.BaseModel):
    id: int = Aliased("maze_id")
    level_name: str = Aliased("name")
    name: str = Aliased("monster_name")
    icon: str = Aliased("monster_icon")


class AnomalyBossRecord(pydantic.BaseModel):
    id: int = Aliased("maze_id")
    has_data: bool = Aliased("has_challenge_record")
    challenge_time: PartialTime
    avatars: list[FloorCharacter]
    buff: ChallengeBuff
    is_hard_mode: bool = Aliased("hard_mode")
    cycles_used: int = Aliased("round_num")
    stars: int = Aliased("star_num")
    has_color_medal: bool = Aliased("finish_color_medal")
    medal_type: str = Aliased("challenge_peak_rank_icon_type")
    medal_icon: str = Aliased("challenge_peak_rank_icon")
    record_unique_key: str


class AnomalyMiniBossRecord(pydantic.BaseModel):
    id: int = Aliased("maze_id")
    has_data: bool = Aliased("has_challenge_record")
    challenge_time: PartialTime | None
    avatars: list[FloorCharacter]
    cycles_used: int = Aliased("round_num")
    stars: int = Aliased("star_num")
    is_quick_clear: bool = Aliased("is_fast")


class AnomalyRecord(pydantic.BaseModel):
    season: AnomalySeason = Aliased("group")
    boss: AnomalyBossInfo = Aliased("boss_info")
    mini_bosses: list[AnomalyMiniBossInfo] = Aliased("mob_infos")
    has_data: bool = Aliased("has_challenge_record")
    challenge_attempts: int = Aliased("battle_num")

    boss_record: AnomalyBossRecord | None = Aliased(default=None)
    mini_boss_records: list[AnomalyMiniBossRecord] = Aliased("mob_records")

    boss_stars: int
    mini_boss_stars: int = Aliased("mob_stars")


class AnomalySummary(pydantic.BaseModel):
    challenge_attempts: int = Aliased("total_battle_num")
    mini_boss_stars: int = Aliased("mob_stars")
    boss_stars: int
    medal_type: str = Aliased("challenge_peak_rank_icon_type")
    medal_icon: str = Aliased("challenge_peak_rank_icon")


class AnomalyPlayer(pydantic.BaseModel):
    server: str
    nickname: str
    level: int
    uid: str = Aliased("role_id")


class AnomalyArbitration(pydantic.BaseModel):
    """Anomaly arbitration challenge."""

    records: list[AnomalyRecord] = Aliased("challenge_peak_records")
    has_more_boss_record: bool
    summary: AnomalySummary | None = Aliased(
        "challenge_peak_best_record_brief", default=None
    )
    player: AnomalyPlayer = Aliased("role")
