import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from client import HSRClient
from enums import ChallengeMode
from notifier import DiscordNotifier, ModeReport

VERSION_FILE = Path("version.txt")

DAILY_MODES = (ChallengeMode.APOC, ChallengeMode.PF, ChallengeMode.AA)


def _build_notifier() -> DiscordNotifier | None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return None

    return DiscordNotifier(webhook_url, discord_id=os.getenv("DISCORD_USER_ID"))


async def run() -> None:
    notifier = _build_notifier()
    reported = False

    try:
        version = VERSION_FILE.read_text().strip()

        client = HSRClient()
        await client.init()

        reports = []
        for mode in DAILY_MODES:
            try:
                result = await client.write_mode(mode, version)
                reports.append(
                    ModeReport(
                        mode=mode, changed=result.changed, diff_lines=result.diff_lines
                    )
                )
            except Exception as error:
                reports.append(ModeReport(mode=mode, error=str(error)))

        if notifier is not None:
            await notifier.send_daily_summary(version, reports)
        reported = True

        failed_modes = [report.mode.value for report in reports if report.error]
        if failed_modes:
            raise RuntimeError(f"Modes failed: {', '.join(failed_modes)}")

    except Exception as error:
        if notifier is not None and not reported:
            await notifier.send_failure("HSR Endgame Automation (setup)", str(error))

        raise


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
