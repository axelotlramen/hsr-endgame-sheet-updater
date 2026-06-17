import os

import gspread
from google.oauth2.service_account import Credentials

from enums import SheetRow


class GoogleSheetsClient:
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self):
        self.creds = Credentials.from_service_account_file(
            os.getenv("SHEET_CREDENTIALS"), scopes=self.SCOPES
        )
        self.gs_client = gspread.authorize(self.creds)

    def insert_rows(self, rows: list[SheetRow]):
        worksheet = self._get_endgame_worksheet()
        worksheet.insert_rows(rows, row=2)

    def _get_endgame_worksheet(self):
        sheet = self.gs_client.open("hsr_endgame")
        return sheet.worksheet("Endgame")
