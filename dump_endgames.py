import argparse
import asyncio
import json

from dotenv import load_dotenv

from lib import ChallengeMode, HSRClient, fetch_endgame_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("mode", choices=[mode.value for mode in ChallengeMode])

    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    mode = ChallengeMode(args.mode)

    client = HSRClient()

    data = await fetch_endgame_data(client.genshin_client, client.uid, mode)

    with open(f"{mode.value}.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
