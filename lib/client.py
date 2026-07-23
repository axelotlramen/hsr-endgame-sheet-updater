import typing

import genshin

from .constants import HSR_SHORT_NAMES
from .enums import ChallengeMode, HSRMode, SheetRow
from .env import require_env
from .models import (
    AnomalyArbitration,
    ApocalypticShadow,
    FloorCharacter,
    MemoryOfChaos,
    PureFiction,
)
from .nanoka import NanokaClient
from .sheets import GoogleSheetsClient, UpsertResult
from .version import VersionResolver

__all__ = ["HSRClient", "fetch_endgame_data"]


async def fetch_endgame_data(
    genshin_client: genshin.Client, uid: int, mode: ChallengeMode
) -> dict:
    """Fetch one mode's raw (`raw=True`) chronicle-challenge response from HoYoLab."""
    match mode:
        case ChallengeMode.APOC:
            return await genshin_client.get_starrail_apc_shadow(uid=uid, raw=True)

        case ChallengeMode.PF:
            return await genshin_client.get_starrail_pure_fiction(uid=uid, raw=True)

        case ChallengeMode.AA:
            return await genshin_client.get_anomaly_arbitration(uid=uid, raw=True)

        case ChallengeMode.MOC:
            return await genshin_client.get_starrail_challenge(uid=uid, raw=True)


class HSRClient:
    def __init__(self) -> None:
        self.genshin_client = genshin.Client()
        self.genshin_client.set_cookies(require_env("HSR_COOKIES"))

        self.uid = int(require_env("HSR_UID"))

        self.nanoka_client = NanokaClient()
        self.gs_client = GoogleSheetsClient()
        self.version_resolver = VersionResolver()

    async def init(self) -> None:
        self.nanoka_characters = await self.nanoka_client.get_characters()

    async def write_mode(self, mode: ChallengeMode) -> UpsertResult:
        data = await fetch_endgame_data(self.genshin_client, self.uid, mode)

        match mode:
            case ChallengeMode.APOC:
                rows = self._build_rows(HSRMode.APOC, ApocalypticShadow(**data))

            case ChallengeMode.PF:
                rows = self._build_rows(HSRMode.PF, PureFiction(**data))

            case ChallengeMode.AA:
                rows = self._build_aa_rows(AnomalyArbitration(**data))

            case ChallengeMode.MOC:
                # Memory of Chaos has no computed score - _preserve_manual_scores fills it
                # in from whatever's already hand-entered on the sheet.
                rows = self._build_rows(
                    HSRMode.MOC, MemoryOfChaos(**data), score_of=lambda _: ""
                )

        return self.gs_client.upsert_rows(rows)

    def _build_rows(
        self,
        mode: HSRMode,
        model: ApocalypticShadow | PureFiction | MemoryOfChaos,
        score_of=lambda node: node.score,
    ) -> list[SheetRow]:
        floor = model.floors[0]

        date = model.seasons[0].begin_time.datetime.date()
        date_str = date.strftime("%m/%d/%Y")
        version = self.version_resolver.resolve(date)

        rows = []

        for side_name, node in self._floor_nodes(floor):
            if node is None:
                continue

            rows.append(
                self._build_row(
                    date_str=date_str,
                    version=version,
                    mode=mode,
                    side_name=side_name,
                    avatars=node.avatars,
                    score=score_of(node),
                )
            )

        return rows

    def _floor_nodes(self, floor) -> list[tuple[str, typing.Any]]:
        return [
            ("Node 1", floor.node_1),
            ("Node 2", floor.node_2),
            ("Node 3", floor.node_3),
        ]

    def _build_aa_rows(self, model: AnomalyArbitration) -> list[SheetRow]:
        record = model.records[0]

        date_str = record.season.end_time.datetime.strftime("%m/%d/%Y")
        version = record.season.game_version

        rows = []

        for i, mini_boss_record in enumerate(record.mini_boss_records, start=1):
            rows.append(
                self._build_row(
                    date_str=date_str,
                    version=version,
                    mode=HSRMode.AA,
                    side_name=f"Knight {i}",
                    avatars=mini_boss_record.avatars,
                    score=mini_boss_record.cycles_used,
                )
            )

        if record.boss_record is not None:
            rows.append(
                self._build_row(
                    date_str=date_str,
                    version=version,
                    mode=HSRMode.AA_KING,
                    side_name="",
                    avatars=record.boss_record.avatars,
                    score=record.boss_record.cycles_used,
                )
            )

        return rows

    def _build_row(
        self,
        date_str: str,
        version: str,
        mode: HSRMode,
        side_name: str,
        avatars: list[FloorCharacter],
        score: int | str,
    ) -> SheetRow:
        return [
            date_str,
            version,
            mode.value,
            side_name,
            "",
            *self._get_avatar_names(avatars),
            score,
        ]

    def _get_avatar_names(self, avatars: list[FloorCharacter]) -> list[str]:
        result = []
        for avatar in avatars:
            name = self.nanoka_characters.get_name(avatar.id)
            result.append(HSR_SHORT_NAMES.get(name, name) if name is not None else name)

        return result
