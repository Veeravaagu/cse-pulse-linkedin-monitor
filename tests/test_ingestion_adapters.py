import json
from datetime import datetime, timezone

from app.services.ingestion.factory import build_ingestion_adapter
from app.services.ingestion.gmail_api_adapter import GmailAPIIngestionAdapter
from app.services.ingestion.mock_adapter import MockGmailIngestionAdapter


def test_mock_adapter_reads_local_payload(tmp_path) -> None:
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(
        json.dumps(
            [
                {
                    "subject": "Prof Maya Lee received an award",
                    "sender": "notifications-noreply@linkedin.com",
                    "snippet": "Award announcement",
                    "body": "https://www.linkedin.com/feed/update/urn:li:activity:123",
                    "received_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        ),
        encoding="utf-8",
    )

    adapter = MockGmailIngestionAdapter(payload_path=str(payload_file))
    records = adapter.fetch_emails()

    assert len(records) == 1
    assert records[0].subject.startswith("Prof Maya Lee")


def test_factory_selects_mock_mode() -> None:
    adapter = build_ingestion_adapter(mode="mock")
    assert isinstance(adapter, MockGmailIngestionAdapter)


def test_factory_selects_gmail_mode() -> None:
    adapter = build_ingestion_adapter(mode="gmail")
    assert isinstance(adapter, GmailAPIIngestionAdapter)


def test_gmail_adapter_scaffold_is_safe_placeholder() -> None:
    adapter = GmailAPIIngestionAdapter(query="from:linkedin.com", max_results=10)
    assert adapter.fetch_emails() == []
