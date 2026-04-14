from pathlib import Path
from typing import Any

from app.models.schemas import ActivityRecord


class GoogleSheetsClient:
    """Push structured activity records to Google Sheets when configured.

    Beginner note:
    - Local development should still work even if Google credentials are missing.
    - That is why this client becomes a no-op unless the feature is explicitly
      enabled and all required config is present.
    """

    def __init__(
        self,
        sheet_id: str,
        worksheet: str,
        *,
        enabled: bool = False,
        credentials_path: str = "",
    ):
        self.enabled = enabled
        self.sheet_id = sheet_id
        self.worksheet = worksheet
        self.credentials_path = credentials_path

    def append_rows(self, rows: list[ActivityRecord]) -> None:
        if not rows or not self.is_configured():
            return None

        values_resource = self._build_values_resource()
        if values_resource is None:
            return None

        values_resource.append(
            spreadsheetId=self.sheet_id,
            range=f"{self.worksheet}!A:J",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": self.map_rows(rows)},
        ).execute()
        return None

    def is_configured(self) -> bool:
        return (
            self.enabled
            and bool(self.sheet_id.strip())
            and bool(self.credentials_path.strip())
            and Path(self.credentials_path).exists()
        )

    def map_rows(self, rows: list[ActivityRecord]) -> list[list[str]]:
        """Convert activity records into a simple row format for Sheets."""

        return [self._to_row(row) for row in rows]

    def _to_row(self, row: ActivityRecord) -> list[str]:
        return [
            row.id,
            row.faculty_name or "",
            row.source_type,
            row.source_url or "",
            row.raw_text,
            row.ai_summary,
            row.category.value,
            str(row.priority),
            row.detected_at.isoformat(),
            row.review_status.value,
        ]

    def _build_values_resource(self) -> Any | None:
        """Create the Google Sheets values client when dependencies exist."""

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            return None

        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            service = build("sheets", "v4", credentials=credentials)
            return service.spreadsheets().values()
        except Exception:
            # Beginner note:
            # if auth setup is incomplete on a local machine, we skip the sync
            # instead of failing the whole ingestion request.
            return None
