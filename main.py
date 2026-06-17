import argparse
import asyncio

from dotenv import load_dotenv

from client import HSRClient


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("mode", choices=["apoc", "moc", "pf", "aa"])

    parser.add_argument("version")

    return parser.parse_args()


async def run():
    args = parse_args()

    client = HSRClient()
    await client.init()

    if args.mode == "apoc":
        await client.write_mode(args.mode, args.version)

    elif args.mode == "moc":
        raise NotImplementedError

    elif args.mode == "pf":
        raise NotImplementedError

    elif args.mode == "aa":
        raise NotImplementedError


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
