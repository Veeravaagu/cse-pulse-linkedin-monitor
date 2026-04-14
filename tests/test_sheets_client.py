from datetime import datetime, timezone

from app.models.schemas import ActivityCategory, ActivityRecord, ReviewStatus
from app.services.sheets_client import GoogleSheetsClient


def _sample_record() -> ActivityRecord:
    return ActivityRecord(
        id="activity-1",
        faculty_name="Alice Johnson",
        source_type="linkedin_email",
        source_url="https://www.linkedin.com/feed/update/1",
        raw_text="Publication accepted in systems journal.",
        ai_summary="Publication accepted.",
        category=ActivityCategory.publication,
        priority=5,
        detected_at=datetime(2026, 4, 14, 12, 0, tzinfo=timezone.utc),
        review_status=ReviewStatus.pending,
    )


def test_google_sheets_client_maps_records_to_rows() -> None:
    client = GoogleSheetsClient("sheet-id", "Sheet1")

    rows = client.map_rows([_sample_record()])

    assert rows == [[
        "activity-1",
        "Alice Johnson",
        "linkedin_email",
        "https://www.linkedin.com/feed/update/1",
        "Publication accepted in systems journal.",
        "Publication accepted.",
        ActivityCategory.publication.value,
        "5",
        "2026-04-14T12:00:00+00:00",
        ReviewStatus.pending.value,
    ]]


def test_google_sheets_client_is_noop_when_not_configured() -> None:
    client = GoogleSheetsClient("", "Sheet1", enabled=False, credentials_path="")

    assert client.is_configured() is False
    assert client.append_rows([_sample_record()]) is None


def test_google_sheets_client_appends_structured_rows(monkeypatch) -> None:
    client = GoogleSheetsClient("sheet-id", "Sheet1", enabled=True, credentials_path="/tmp/fake.json")
    captured: dict[str, object] = {}

    class FakeRequest:
        def execute(self) -> None:
            captured["executed"] = True
            return None

    class FakeValuesResource:
        def append(self, **kwargs):
            captured.update(kwargs)
            return FakeRequest()

    monkeypatch.setattr(client, "is_configured", lambda: True)
    monkeypatch.setattr(client, "_build_values_resource", lambda: FakeValuesResource())

    client.append_rows([_sample_record()])

    assert captured["spreadsheetId"] == "sheet-id"
    assert captured["range"] == "Sheet1!A:J"
    assert captured["valueInputOption"] == "RAW"
    assert captured["insertDataOption"] == "INSERT_ROWS"
    assert captured["body"] == {"values": client.map_rows([_sample_record()])}
    assert captured["executed"] is True


def test_google_sheets_client_is_noop_when_client_builder_returns_none(tmp_path, monkeypatch) -> None:
    credentials_path = tmp_path / "service-account.json"
    credentials_path.write_text("{}", encoding="utf-8")
    client = GoogleSheetsClient(
        "sheet-id",
        "Sheet1",
        enabled=True,
        credentials_path=str(credentials_path),
    )

    monkeypatch.setattr(client, "_build_values_resource", lambda: None)

    assert client.append_rows([_sample_record()]) is None
