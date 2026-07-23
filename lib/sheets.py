from dataclasses import dataclass, field

import gspread
from google.oauth2.service_account import Credentials

from .enums import HSRMode, SheetRow
from .env import require_env

__all__ = ["UpsertResult", "GoogleSheetsClient"]

DATE_COL, VERSION_COL, MODE_COL, SIDE_COL, SCORE_COL = 0, 1, 2, 3, -1

# Display order on the sheet: newest version on top; within a version, AA above its own
# King row, then MoC, then PF, then Apocalyptic Shadow.
MODE_ORDER = [
    HSRMode.AA.value,
    HSRMode.AA_KING.value,
    HSRMode.MOC.value,
    HSRMode.PF.value,
    HSRMode.APOC.value,
]


@dataclass
class UpsertResult:
    changed: bool
    diff_lines: list[str] = field(default_factory=list)
    version: str | None = None


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
        """Replace any existing rows for the same (version, mode) and report what changed.

        Rows are kept sorted on the sheet with the newest version on top, and - within a
        version - in MODE_ORDER (AA above its King row, then MoC, then PF, then Apocalyptic
        Shadow). A version/mode this call doesn't touch (e.g. an older version's rows) is
        left in place, so old data isn't lost when a mode moves on to a new version.
        """
        if not rows:
            return UpsertResult(changed=False)

        worksheet = self._get_endgame_worksheet()

        version = rows[0][VERSION_COL]
        mode_values = list(dict.fromkeys(row[MODE_COL] for row in rows))

        previous_rows: list[SheetRow] = []
        for mode_value in mode_values:
            previous_rows.extend(
                self._delete_matching_rows(worksheet, version, mode_value)
            )

        rows = _preserve_manual_scores(previous_rows, rows)

        insert_at = self._find_insert_row(worksheet, version, mode_values)
        worksheet.insert_rows(rows, row=insert_at)

        diff_lines = _diff_rows(previous_rows, rows)
        return UpsertResult(
            changed=bool(diff_lines), diff_lines=diff_lines, version=version
        )

    def _delete_matching_rows(
        self, worksheet: gspread.Worksheet, version: str, mode_value: str
    ) -> list[SheetRow]:
        values = worksheet.get_all_values()

        matching = [
            (row_number, row)
            for row_number, row in enumerate(values, start=1)
            if row[VERSION_COL] == version and row[MODE_COL] == mode_value
        ]

        for row_number, _ in reversed(matching):
            worksheet.delete_rows(row_number)

        return [row for _, row in matching]

    def _find_insert_row(
        self, worksheet: gspread.Worksheet, version: str, mode_values: list[str]
    ) -> int:
        """Return the row number where a (version, mode_values) block belongs, sheet-sorted."""
        group_key = min(_sort_key(version, mode_value) for mode_value in mode_values)

        values = worksheet.get_all_values()
        for row_number, row in enumerate(values, start=1):
            if row_number == 1:
                continue

            if _sort_key(row[VERSION_COL], row[MODE_COL]) > group_key:
                return row_number

        return len(values) + 1

    def get_all_rows(self) -> list[SheetRow]:
        """Return every row in the Endgame worksheet, including the header row."""
        return self._get_endgame_worksheet().get_all_values()

    def _get_endgame_worksheet(self) -> gspread.Worksheet:
        sheet = self.gs_client.open(self.SHEET_NAME)
        return sheet.worksheet(self.WORKSHEET_NAME)


def _sort_key(version: str, mode_value: str) -> tuple[tuple[int, int], int]:
    """Sort key for a (version, mode) block: newest version first, then MODE_ORDER."""
    major, minor = (int(part) for part in version.split("."))
    return (-major, -minor), MODE_ORDER.index(mode_value)


def _preserve_manual_scores(
    previous_rows: list[SheetRow], new_rows: list[SheetRow]
) -> list[SheetRow]:
    """Keep a manually-entered score in place when the automation has none to write for that side."""
    previous_by_side = {row[SIDE_COL]: row for row in previous_rows}

    preserved = []
    for row in new_rows:
        previous = previous_by_side.get(row[SIDE_COL])
        if row[SCORE_COL] == "" and previous is not None and previous[SCORE_COL] != "":
            row = [*row[:SCORE_COL], previous[SCORE_COL]]
        preserved.append(row)

    return preserved


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
