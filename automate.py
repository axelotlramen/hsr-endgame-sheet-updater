import asyncio
from pathlib import Path

from dotenv import load_dotenv

from lib import ChallengeMode, HSRClient, ModeReport, notifier_from_env

VERSION_FILE = Path("version.txt")

DAILY_MODES = (ChallengeMode.APOC, ChallengeMode.PF, ChallengeMode.AA)


async def run() -> None:
    notifier = notifier_from_env()
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
