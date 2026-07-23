import argparse
import asyncio

from dotenv import load_dotenv

from lib import ChallengeMode, HSRClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("mode", choices=[mode.value for mode in ChallengeMode])

    return parser.parse_args()


async def run() -> None:
    args = parse_args()
    mode = ChallengeMode(args.mode)

    client = HSRClient()
    await client.init()

    await client.write_mode(mode)


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
