import os

import genshin

from enums import HSRMode, SheetRow
from nanoka import NanokaClient
from sheets import GoogleSheetsClient
from utils import format_date


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
            mode = HSRMode.APOC
            model = await self.genshin_client.get_starrail_apc_shadow(uid=self.uid)

        else:
            raise ValueError(f"Unknown mode: {mode}")

        rows = self._build_rows(mode, model, version)
        self.gs_client.insert_rows(rows)

    def _build_rows(self, mode: HSRMode, model, version: str) -> list[SheetRow]:
        floor = model.floors[0]

        date_str = format_date(floor.last_update_time)

        rows = []

        nodes = [("Side 1", floor.node_1), ("Side 2", floor.node_2)]

        if floor.node_3 is not None:
            nodes.append(("Side 3", floor.node_3))

        for side_name, node in nodes:
            rows.append(
                self._build_row(
                    date_str=date_str,
                    version=version,
                    mode=mode,
                    side_name=side_name,
                    node=node,
                )
            )

        return rows

    def _build_row(
        self, date_str: str, version: str, mode: HSRMode, side_name: str, node
    ) -> SheetRow:
        return [
            date_str,
            version,
            mode.value,
            side_name,
            "",
            *self._get_avatar_names(node.avatars),
            node.score,
        ]

    def _get_avatar_names(
        self, avatars: list[genshin.models.FloorCharacter]
    ) -> list[str]:
        result = []
        for avatar in avatars:
            result.append(self.nanoka_characters.get_name(avatar.id))

        return result
