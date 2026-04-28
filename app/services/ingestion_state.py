import json
from datetime import datetime
from pathlib import Path


class IngestionStateStore:
    """Small JSON cursor store for local/dev ingestion runs."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def get_last_successful_ingestion_at(self) -> datetime | None:
        if not self.file_path.exists():
            return None

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

        value = data.get("last_successful_ingestion_at")
        if not isinstance(value, str) or not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def set_last_successful_ingestion_at(self, value: datetime) -> None:
        payload = {"last_successful_ingestion_at": value.isoformat()}
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
