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

__all__ = ["HSRClient"]


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
        match mode:
            case ChallengeMode.APOC:
                apoc_data = await self.genshin_client.get_starrail_apc_shadow(
                    uid=self.uid, raw=True
                )
                model = ApocalypticShadow(**apoc_data)
                rows = self._build_rows(HSRMode.APOC, model)

            case ChallengeMode.PF:
                pf_data = await self.genshin_client.get_starrail_pure_fiction(
                    uid=self.uid, raw=True
                )
                model = PureFiction(**pf_data)
                rows = self._build_rows(HSRMode.PF, model)

            case ChallengeMode.AA:
                aa_data = await self.genshin_client.get_anomaly_arbitration(
                    uid=self.uid, raw=True
                )
                model = AnomalyArbitration(**aa_data)
                rows = self._build_aa_rows(model)

            case ChallengeMode.MOC:
                moc_data = await self.genshin_client.get_starrail_challenge(
                    uid=self.uid, raw=True
                )
                model = MemoryOfChaos(**moc_data)
                rows = self._build_moc_rows(model)

        return self.gs_client.upsert_rows(rows)

    def _build_rows(
        self, mode: HSRMode, model: ApocalypticShadow | PureFiction
    ) -> list[SheetRow]:
        floor = model.floors[0]

        date = model.seasons[0].begin_time.datetime.date()
        date_str = date.strftime("%m/%d/%Y")
        version = self.version_resolver.resolve(date)

        rows = []

        nodes = [
            ("Node 1", floor.node_1),
            ("Node 2", floor.node_2),
            ("Node 3", floor.node_3),
        ]

        for side_name, node in nodes:
            if node is None:
                continue

            rows.append(
                self._build_row(
                    date_str=date_str,
                    version=version,
                    mode=mode,
                    side_name=side_name,
                    avatars=node.avatars,
                    score=node.score,
                )
            )

        return rows

    def _build_aa_rows(self, model: AnomalyArbitration) -> list[SheetRow]:
        record = model.records[0]

        date_str = record.season.end_time.datetime.strftime("%m/%d/%Y")
        version = self.version_resolver.resolve(
            record.season.begin_time.datetime.date()
        )

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

    def _build_moc_rows(self, model: MemoryOfChaos) -> list[SheetRow]:
        floor = model.floors[0]

        date = model.seasons[0].begin_time.datetime.date()
        date_str = date.strftime("%m/%d/%Y")
        version = self.version_resolver.resolve(date)

        rows = []

        nodes = [
            ("Node 1", floor.node_1),
            ("Node 2", floor.node_2),
            ("Node 3", floor.node_3),
        ]

        for side_name, node in nodes:
            if node is None:
                continue

            rows.append(
                self._build_row(
                    date_str=date_str,
                    version=version,
                    mode=HSRMode.MOC,
                    side_name=side_name,
                    avatars=node.avatars,
                    score="",
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
