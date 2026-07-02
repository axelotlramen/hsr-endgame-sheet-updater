import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from client import HSRClient


class AutomationClient:
    def __init__(self) -> None:
        self.hsr_client = HSRClient()

    async def get_endgame(self):
        apoc_raw = await self.hsr_client.genshin_client.get_starrail_apc_shadow(uid=self.hsr_client.uid, raw=True)

        Path("apoc.json").write_text(json.dumps(apoc_raw, indent=2, ensure_ascii=False))

        pf_raw = await self.hsr_client.genshin_client.get_starrail_pure_fiction(uid=self.hsr_client.uid, raw=True)

        Path("pf.json").write_text(json.dumps(pf_raw, indent=2, ensure_ascii=False))

        moc_raw = await self.hsr_client.genshin_client.get_starrail_challenge(uid=self.hsr_client.uid, raw=True)

        Path("moc.json").write_text(json.dumps(moc_raw, indent=2, ensure_ascii=False))

        aa_raw = await self.hsr_client.genshin_client.get_anomaly_arbitration(uid=self.hsr_client.uid, raw=True)

        Path("aa.json").write_text(json.dumps(aa_raw, indent=2, ensure_ascii=False))

    async def get_random(self):
        apoc_data = await self.hsr_client.genshin_client.get_starrail_pure_fiction(uid=self.hsr_client.uid, raw=True)

        # apoc_model = ApocalypticShadow(**apoc_data)

        Path("pf.json").write_text(
            json.dumps(apoc_data, indent=2, ensure_ascii=False)
        )

    async def get_random_2(self):
        game_modes = await self.hsr_client.genshin_client.get_starrail_lineup_game_modes()

        moc_stage_12 = self.hsr_client.genshin_client.get_starrail_lineup_floor(game_modes, type="Chasm", floor=12)
        print(moc_stage_12)

        if moc_stage_12 is None:
            return "Nothing happened"

        schedules = await self.hsr_client.genshin_client.get_starrail_lineup_schedules("Chasm")
        # for schedule in schedules:
        #     print(f"{schedule.id} - {schedule.name} ({schedule.start_time} ~ {schedule.end_time})")

        current = schedules[0]
        print(current)
        next_page_token = None
        for _ in range(5):
            page = await self.hsr_client.genshin_client.get_starrail_lineups(tag_id=moc_stage_12.id, group_id=current.id, type="Chasm", next_page_token=next_page_token)
            print(page)

            for lineup in page.lineups:
                print(lineup)
            
            next_page_token = page.next_page_token

        return "Hi"



    def get_version(self) -> str:
        return Path("version.txt").read_text().strip()

async def run():
    client = AutomationClient()

    await client.get_endgame()
    
if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())