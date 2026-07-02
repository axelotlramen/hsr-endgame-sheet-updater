import os

import genshin

from enums import HSRMode, SheetRow
from models.aa import AnomalyArbitration
from models.apoc import ApocalypticShadow, FloorCharacter
from models.pf import PureFiction
from nanoka import NanokaClient
from sheets import GoogleSheetsClient


class HSRClient:
    def __init__(self) -> None:
        self.genshin_client = genshin.Client()
        self.genshin_client.set_cookies(os.getenv("HSR_COOKIES"))

        self.uid = int(os.getenv("HSR_UID") or "")

        self.nanoka_client = NanokaClient()
        self.gs_client = GoogleSheetsClient()

    async def init(self) -> None:
        self.nanoka_characters = await self.nanoka_client.get_characters()

    async def write_mode(self, mode: str, version: str) -> None:
        if mode == "apoc":
            apoc_data = await self.genshin_client.get_starrail_apc_shadow(uid=self.uid, raw=True)
            model = ApocalypticShadow(**apoc_data)
            rows = self._build_rows(HSRMode.APOC, model, version)

        elif mode == "pf":
            pf_data = await self.genshin_client.get_starrail_pure_fiction(uid=self.uid, raw=True)
            model = PureFiction(**pf_data)
            rows = self._build_rows(HSRMode.PF, model, version)

        elif mode == "aa":
            aa_data = await self.genshin_client.get_anomaly_arbitration(uid=self.uid, raw=True)
            model = AnomalyArbitration(**aa_data)
            rows = self._build_aa_rows(model, version)

        else:
            raise ValueError(f"Unknown mode: {mode}")

        self.gs_client.insert_rows(rows)

    def _build_rows(
        self, mode: HSRMode, model: ApocalypticShadow | PureFiction, version: str
    ) -> list[SheetRow]:
        floor = model.floors[0]

        date = model.seasons[0].begin_time
        date_str = date.datetime.strftime("%m/%d/%Y")

        rows = []

        nodes = [("Side 1", floor.node_1), ("Side 2", floor.node_2), ("Side 3", floor.node_3)]

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

    def _build_aa_rows(self, model: AnomalyArbitration, version: str) -> list[SheetRow]:
        record = model.records[0]

        date_str = record.season.end_time.datetime.strftime("%m/%d/%Y")

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
        score: int,
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

    def _get_avatar_names(
        self, avatars: list[FloorCharacter]
    ) -> list[str]:
        result = []
        for avatar in avatars:
            result.append(self.nanoka_characters.get_name(avatar.id))

        return result
