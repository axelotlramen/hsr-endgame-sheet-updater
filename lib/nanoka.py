import httpx

from .constants import HSR_PATHS

__all__ = ["NanokaClient", "NanokaCharacterData"]


class NanokaClient:
    BASE_URL = "https://static.nanoka.cc"

    DEFAULT_HEADERS = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8",
        "cache-control": "no-cache",
        "origin": "https://hsr.nanoka.cc",
        "pragma": "no-cache",
        "referer": "https://hsr.nanoka.cc/",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36 OPR/132.0.0.0"
        ),
    }

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL, headers=self.DEFAULT_HEADERS, timeout=30.0
        )

    async def close(self):
        await self.client.aclose()

    async def get_characters(self, version: str = "4.4.52") -> "NanokaCharacterData":
        response = await self.client.get(f"/hsr/{version}/character.json")

        response.raise_for_status()

        return NanokaCharacterData(response.json())


class NanokaCharacterData:
    SPECIAL_NAME_RULE = {
        "{NICKNAME}": lambda self, character_id: (
            f"{self.get_path(character_id)} Trailblazer"
        ),
        "March 7th": lambda self, character_id: (
            f"{self.get_path(character_id)} March 7th"
        ),
    }

    def __init__(self, data: dict):
        self.data = data

    def get_character(self, character_id: str | int) -> dict | None:
        return self.data.get(str(character_id))

    def get_name(self, character_id: str | int) -> str | None:
        character = self.get_character(character_id)

        if character is None:
            return None

        name = character.get("en")

        rule = self.SPECIAL_NAME_RULE.get(str(name))

        if rule:
            return rule(self, character_id)

        return name

    def get_path(self, character_id: str | int) -> str | None:
        character = self.get_character(character_id)

        if character is None:
            return None

        return HSR_PATHS.get(character.get("baseType", ""), "")

    def get_all_characters(self) -> dict:
        return self.data

    def __len__(self) -> int:
        return len(self.data)
