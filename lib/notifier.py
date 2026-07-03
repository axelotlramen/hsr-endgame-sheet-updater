import datetime
import os
from dataclasses import dataclass, field

import httpx

from .enums import ChallengeMode

__all__ = ["ModeReport", "UsageChange", "DiscordNotifier", "notifier_from_env"]

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


@dataclass
class UsageChange:
    """A single unit's (or unit-in-endgame's) usage count/average score change."""

    label: str
    old_uses: int
    new_uses: int
    old_avg_score: float | None = None
    new_avg_score: float | None = None


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

    async def send_usage_update(
        self,
        overall_changes: list[UsageChange],
        by_endgame_changes: list[UsageChange],
        top_units: list[tuple[str, int]],
        current_patch: float,
    ) -> None:
        """Post the weekly usage report: what changed since current_patch, plus a top-10 embed.

        Always sends, whether or not anything changed - the content varies, not whether a
        message is sent at all, so a quiet week still confirms the workflow ran.
        """
        has_changes = bool(overall_changes or by_endgame_changes)

        content = (
            f"📈 Weekly character usage update — changes since patch {current_patch}."
            if has_changes
            else f"✅ Weekly character usage update — no changes since patch {current_patch}, still running fine."
        )

        change_fields = []
        if overall_changes:
            table = _render_table(
                ["Unit", f"Uses Since {current_patch}"],
                [
                    [change.label, f"{change.old_uses} → {change.new_uses}"]
                    for change in overall_changes
                ],
            )
            change_fields.append({"name": "All Endgames", "value": table})
        if by_endgame_changes:
            table = _render_table(
                ["Endgame / Unit", "Uses", "Avg Score"],
                [
                    [
                        change.label,
                        f"{change.old_uses} → {change.new_uses}",
                        _format_avg_change(change.old_avg_score, change.new_avg_score),
                    ]
                    for change in by_endgame_changes
                ],
            )
            change_fields.append({"name": "Per Endgame", "value": table})
        if not change_fields:
            change_fields.append(
                {
                    "name": "Status",
                    "value": f"No usage changes since patch {current_patch}.",
                }
            )

        embeds = [
            {
                "title": f"Weekly Usage Changes (Since Patch {current_patch})",
                "color": GREEN_EMBED,
                "fields": change_fields,
                "timestamp": _now_iso(),
            }
        ]

        if top_units:
            leaderboard = _render_table(
                ["#", "Unit", f"Uses Since {current_patch}"],
                [
                    [str(rank), unit, str(uses)]
                    for rank, (unit, uses) in enumerate(top_units, start=1)
                ],
            )
            embeds.append(
                {
                    "title": f"Top {len(top_units)} Units Since Patch {current_patch}",
                    "color": GREEN_EMBED,
                    "description": leaderboard,
                    "timestamp": _now_iso(),
                }
            )

        await self._post({"content": content, "embeds": embeds})

    async def _post(self, payload: dict) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()


def notifier_from_env() -> "DiscordNotifier | None":
    """Build a DiscordNotifier from DISCORD_WEBHOOK_URL/DISCORD_USER_ID, or None if unset."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return None

    return DiscordNotifier(webhook_url, discord_id=os.getenv("DISCORD_USER_ID"))


def _render_table(headers: list[str], rows: list[list[str]], limit: int = 1000) -> str:
    """Render a monospace table (in a code block) for Discord, truncated to fit one field."""
    widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def format_row(cells: list[str]) -> str:
        return "  ".join(cell.ljust(width) for cell, width in zip(cells, widths))

    lines = [format_row(headers), format_row(["-" * width for width in widths])]
    lines.extend(format_row(row) for row in rows)

    body = "\n".join(lines)
    if len(body) > limit:
        truncated = body[:limit].rsplit("\n", 1)[0]
        body = f"{truncated}\n… ({len(rows)} rows total)"

    return f"```\n{body}\n```"


def _format_avg_score(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def _format_avg_change(old_value: float | None, new_value: float | None) -> str:
    return f"{_format_avg_score(old_value)} → {_format_avg_score(new_value)}"


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
