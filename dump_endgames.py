import argparse
import asyncio
import json
import typing

from dotenv import load_dotenv

from lib import ChallengeMode, HSRClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("mode", choices=[mode.value for mode in ChallengeMode])

    return parser.parse_args()


async def dump_mode(
    client: HSRClient, mode: ChallengeMode
) -> typing.Mapping[str, typing.Any]:
    match mode:
        case ChallengeMode.APOC:
            return await client.genshin_client.get_starrail_apc_shadow(
                uid=client.uid, raw=True
            )

        case ChallengeMode.PF:
            return await client.genshin_client.get_starrail_pure_fiction(
                uid=client.uid, raw=True
            )

        case ChallengeMode.AA:
            return await client.genshin_client.get_anomaly_arbitration(
                uid=client.uid, raw=True
            )

        case ChallengeMode.MOC:
            return await client.genshin_client.get_starrail_challenge(
                uid=client.uid, raw=True
            )


async def run() -> None:
    args = parse_args()
    mode = ChallengeMode(args.mode)

    client = HSRClient()

    data = await dump_mode(client, mode)

    with open(f"{mode.value}.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
