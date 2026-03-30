import json
from pathlib import Path

from app.models.schemas import RawEmail


class MockGmailIngestionAdapter:
    """Loads sample email payloads from a local JSON file for development/tests."""

    def __init__(self, payload_path: str = "data/mock_emails/linkedin_notifications.json") -> None:
        self.payload_path = Path(payload_path)

    def fetch_emails(self) -> list[RawEmail]:
        if not self.payload_path.exists():
            return []

        raw_payload = json.loads(self.payload_path.read_text(encoding="utf-8"))
        return [RawEmail.model_validate(item) for item in raw_payload]
