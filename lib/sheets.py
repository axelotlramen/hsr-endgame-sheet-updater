from dataclasses import dataclass, field

import gspread
from google.oauth2.service_account import Credentials

from .enums import SheetRow
from .env import require_env

__all__ = ["UpsertResult", "GoogleSheetsClient"]

DATE_COL, VERSION_COL, MODE_COL, SIDE_COL, SCORE_COL = 0, 1, 2, 3, -1


@dataclass
class UpsertResult:
    changed: bool
    diff_lines: list[str] = field(default_factory=list)


class GoogleSheetsClient:
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    SHEET_NAME = "hsr_endgame"
    WORKSHEET_NAME = "Endgame"

    def __init__(self):
        self.creds = Credentials.from_service_account_file(
            require_env("SHEET_CREDENTIALS"), scopes=self.SCOPES
        )
        self.gs_client = gspread.authorize(self.creds)

    def upsert_rows(self, rows: list[SheetRow]) -> UpsertResult:
        """Replace any existing rows for the same (date, version, mode) and report what changed."""
        if not rows:
            return UpsertResult(changed=False)

        worksheet = self._get_endgame_worksheet()

        keys = {(row[DATE_COL], row[VERSION_COL], row[MODE_COL]) for row in rows}
        previous_rows: list[SheetRow] = []
        for date_str, version, mode_value in keys:
            previous_rows.extend(
                self._delete_matching_rows(worksheet, date_str, version, mode_value)
            )

        worksheet.insert_rows(rows, row=2)

        diff_lines = _diff_rows(previous_rows, rows)
        return UpsertResult(changed=bool(diff_lines), diff_lines=diff_lines)

    def _delete_matching_rows(
        self, worksheet: gspread.Worksheet, date_str: str, version: str, mode_value: str
    ) -> list[SheetRow]:
        values = worksheet.get_all_values()

        matching = [
            (row_number, row)
            for row_number, row in enumerate(values, start=1)
            if row[DATE_COL : MODE_COL + 1] == [date_str, version, mode_value]
        ]

        for row_number, _ in reversed(matching):
            worksheet.delete_rows(row_number)

        return [row for _, row in matching]

    def get_all_rows(self) -> list[SheetRow]:
        """Return every row in the Endgame worksheet, including the header row."""
        return self._get_endgame_worksheet().get_all_values()

    def _get_endgame_worksheet(self) -> gspread.Worksheet:
        sheet = self.gs_client.open(self.SHEET_NAME)
        return sheet.worksheet(self.WORKSHEET_NAME)


def _diff_rows(previous_rows: list[SheetRow], new_rows: list[SheetRow]) -> list[str]:
    """Compare rows by side, returning one human-readable line per new/changed side."""
    previous_by_side = {row[SIDE_COL]: row for row in previous_rows}

    lines = []
    for row in new_rows:
        side = row[SIDE_COL] or "Overall"
        previous = previous_by_side.get(row[SIDE_COL])

        if previous is None:
            lines.append(f"🆕 {side}: {row[SCORE_COL]}")
        elif [str(value) for value in previous] != [str(value) for value in row]:
            lines.append(f"{side}: {previous[SCORE_COL]} → {row[SCORE_COL]}")

    return lines
