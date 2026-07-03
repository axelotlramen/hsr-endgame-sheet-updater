import datetime
from dataclasses import dataclass, field

import httpx

from enums import ChallengeMode

RED_EMBED = 15548997
GREEN_EMBED = 5763719

MODE_LABELS = {
    ChallengeMode.APOC: "Apocalyptic Shadow",
    ChallengeMode.PF: "Pure Fiction",
    ChallengeMode.AA: "Anomaly Arbitration",
    ChallengeMode.MOC: "Memory of Chaos",
}


@dataclass
class ModeReport:
    mode: ChallengeMode
    changed: bool = False
    diff_lines: list[str] = field(default_factory=list)
    error: str | None = None


class DiscordNotifier:
    def __init__(self, webhook_url: str, discord_id: str | None = None) -> None:
        self.webhook_url = webhook_url
        self.discord_id = discord_id

    async def send_failure(self, task_name: str, error_message: str) -> None:
        """Post a failure embed to the webhook, pinging discord_id if one is set."""
        mention = f"<@{self.discord_id}> " if self.discord_id else ""

        embed = {
            "title": "Task Failure",
            "description": f"❌ **{task_name} Failed**\n\n```{error_message}```",
            "color": RED_EMBED,
            "timestamp": _now_iso(),
        }

        await self._post(
            {"content": f"{mention}HSR endgame automation failed!", "embeds": [embed]}
        )

    async def send_daily_summary(self, version: str, reports: list[ModeReport]) -> None:
        """Post one embed summarizing every mode's result, whether or not anything changed."""
        has_errors = any(report.error for report in reports)
        has_changes = any(report.changed for report in reports)

        if has_errors:
            mention = f"<@{self.discord_id}> " if self.discord_id else ""
            content = f"{mention}⚠️ Daily HSR update finished with errors."
        elif has_changes:
            content = "📊 Daily HSR update — new results today."
        else:
            content = "✅ Daily HSR update — everything is running fine, no changes."

        fields = [_report_field(report) for report in reports]

        embed = {
            "title": "Daily HSR Endgame Update",
            "description": f"**Version:** {version}",
            "color": RED_EMBED if has_errors else GREEN_EMBED,
            "fields": fields,
            "timestamp": _now_iso(),
        }

        await self._post({"content": content, "embeds": [embed]})

    async def _post(self, payload: dict) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()


def _report_field(report: ModeReport) -> dict:
    label = MODE_LABELS.get(report.mode, report.mode.value)

    if report.error:
        value = f"❌ ```{report.error}```"
    elif report.diff_lines:
        value = "\n".join(report.diff_lines)
    else:
        value = "No changes"

    return {"name": label, "value": value, "inline": False}


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
