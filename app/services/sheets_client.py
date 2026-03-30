from app.models.schemas import ActivityRecord


class GoogleSheetsClient:
    """Scaffold for pushing structured records to Google Sheets.

    In mock/student mode this is a no-op. Replace `append_rows` internals after
    setting up a Google service account and sheet permissions.
    """

    def __init__(self, sheet_id: str, worksheet: str):
        self.sheet_id = sheet_id
        self.worksheet = worksheet

    def append_rows(self, rows: list[ActivityRecord]) -> None:
        # TODO: Integrate gspread/google-api-python-client.
        # Intentionally no-op to keep local setup simple.
        _ = rows
        return None
