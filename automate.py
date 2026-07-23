import asyncio

from dotenv import load_dotenv

from lib import (
    MODE_LABELS,
    AutomationLogger,
    ChallengeMode,
    HSRClient,
    ModeReport,
    notifier_from_env,
)

# Each mode's rows are inserted right after the header, so processing order is the reverse of
# the resulting on-sheet order (last processed ends up on top): this yields AA, MOC, PF, APOC.
DAILY_MODES = (
    ChallengeMode.APOC,
    ChallengeMode.PF,
    ChallengeMode.MOC,
    ChallengeMode.AA,
)

logger = AutomationLogger(__name__)


async def run() -> None:
    notifier = notifier_from_env()
    reported = False

    try:
        logger.info("Starting daily HSR endgame automation")

        client = HSRClient()
        await client.init()

        reports = []
        for mode in DAILY_MODES:
            label = MODE_LABELS.get(mode, mode.value)
            logger.info(f"Fetching {label}...")
            try:
                result = await client.write_mode(mode)
                reports.append(
                    ModeReport(
                        mode=mode,
                        changed=result.changed,
                        diff_lines=result.diff_lines,
                        version=result.version,
                    )
                )
                if result.changed:
                    logger.info(
                        f"{label}: updated ({len(result.diff_lines)} change(s))"
                    )
                else:
                    logger.info(f"{label}: no changes")
            except Exception as error:
                reports.append(ModeReport(mode=mode, error=str(error)))
                logger.error(f"{label}: failed - {error}")

        if notifier is not None:
            await notifier.send_daily_summary(reports)
            logger.info("Sent daily summary to Discord")
        else:
            logger.warning(
                "DISCORD_WEBHOOK_URL not set - skipping Discord notification"
            )
        reported = True

        failed_modes = [report.mode.value for report in reports if report.error]
        if failed_modes:
            raise RuntimeError(f"Modes failed: {', '.join(failed_modes)}")

        logger.info("Daily HSR endgame automation finished successfully")

    except Exception as error:
        logger.error(f"Automation failed: {error}")

        if notifier is not None and not reported:
            await notifier.send_failure("HSR Endgame Automation (setup)", str(error))

        raise


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
