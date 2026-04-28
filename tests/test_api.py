import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.schemas import ActivityCategory, RawEmail, ReviewStatus
from app.services.public_fetch_mode import PublicFetchModeStore
from app.services.storage import JSONStorageService


def _seed_activity_file(file_path: str) -> None:
    now = datetime.now(timezone.utc)
    payload = [
        {
            "id": "activity-1",
            "faculty_name": "Alice Johnson",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/1",
            "raw_text": "Publication accepted in systems journal.",
            "ai_summary": "Publication accepted.",
            "category": ActivityCategory.publication.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=2)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "activity-2",
            "faculty_name": "Bob Lee",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/2",
            "raw_text": "Workshop event announced.",
            "ai_summary": "Workshop event.",
            "category": ActivityCategory.talk_event.value,
            "priority": 3,
            "detected_at": now.isoformat(),
            "review_status": ReviewStatus.reviewed.value,
        },
        {
            "id": "activity-3",
            "faculty_name": "Carla Smith",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/3",
            "raw_text": "Award received for research.",
            "ai_summary": "Research award.",
            "category": ActivityCategory.award.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=1)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
    ]
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _seed_dashboard_window_activity_file(file_path: str) -> None:
    now = datetime.now(timezone.utc)
    payload = [
        {
            "id": "recent-pending",
            "faculty_name": "Recent Pending",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/recent-pending",
            "raw_text": "Recent pending update.",
            "ai_summary": "Recent pending update.",
            "category": ActivityCategory.publication.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=1)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "recent-approved",
            "faculty_name": "Recent Approved",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/recent-approved",
            "raw_text": "Recent approved update.",
            "ai_summary": "Recent approved update.",
            "category": ActivityCategory.award.value,
            "priority": 4,
            "detected_at": (now - timedelta(days=3)).isoformat(),
            "review_status": ReviewStatus.approved.value,
        },
        {
            "id": "old-rejected",
            "faculty_name": "Old Rejected",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/old-rejected",
            "raw_text": "Old rejected update.",
            "ai_summary": "Old rejected update.",
            "category": ActivityCategory.other.value,
            "priority": 2,
            "detected_at": (now - timedelta(days=45)).isoformat(),
            "review_status": ReviewStatus.rejected.value,
        },
    ]
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _seed_public_activity_file(file_path: str) -> None:
    now = datetime.now(timezone.utc)
    payload = [
        {
            "id": "public-pending",
            "faculty_name": "Pending Activity",
            "source_type": "ub_cse_email",
            "source_url": "https://engineering.buffalo.edu/pending",
            "raw_text": "Pending activity.",
            "ai_summary": "Pending activity.",
            "category": ActivityCategory.department_news.value,
            "priority": 3,
            "detected_at": now.isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "public-approved",
            "faculty_name": "Approved Activity",
            "source_type": "ub_cse_email",
            "source_url": "https://engineering.buffalo.edu/approved",
            "raw_text": "Approved activity.",
            "ai_summary": "Approved activity.",
            "category": ActivityCategory.award.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=1)).isoformat(),
            "review_status": ReviewStatus.approved.value,
        },
        {
            "id": "public-rejected",
            "faculty_name": "Rejected Activity",
            "source_type": "ub_cse_email",
            "source_url": "https://engineering.buffalo.edu/rejected",
            "raw_text": "Rejected activity.",
            "ai_summary": "Rejected activity.",
            "category": ActivityCategory.other.value,
            "priority": 2,
            "detected_at": (now - timedelta(days=2)).isoformat(),
            "review_status": ReviewStatus.rejected.value,
        },
    ]
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _configure_public_activity_test(data_file: Path, mode_file: Path) -> tuple[object, object]:
    original_storage = routes.storage
    original_mode_store = routes.public_fetch_mode_store
    routes.storage = JSONStorageService(str(data_file))
    routes.public_fetch_mode_store = PublicFetchModeStore(str(mode_file))
    return original_storage, original_mode_store


def test_health_reports_storage_status_and_activity_count(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["storage"] == "ok"
        assert data["activity_count"] == 3
    finally:
        routes.storage = original_storage


def test_dashboard_page_loads() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "CSE Activity Monitoring Dashboard" in response.text
    assert "Activity Inbox" in response.text
    assert 'data-status-tab="pending"' in response.text
    assert 'data-status-tab="approved"' in response.text
    assert 'data-status-tab="rejected"' in response.text
    assert "Mark reviewed" not in response.text


def test_dashboard_ingestion_button_uses_real_ingest_endpoint() -> None:
    dashboard_js = Path("app/static/dashboard.js").read_text(encoding="utf-8")

    assert 'fetchPayload("/ingest", { method: "POST" })' in dashboard_js
    assert "/ingest/mock" not in dashboard_js
    assert "/demo" not in dashboard_js


def test_ingest_endpoint_uses_gmail_ingestion_mode(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    def fake_run_ingestion(mode: str | None = None) -> object:
        captured["mode"] = mode
        return {"ingested_count": 0, "activities": []}

    monkeypatch.setattr(routes.settings, "ingestion_mode", "mock")
    monkeypatch.setattr(routes, "_run_ingestion", fake_run_ingestion)

    client = TestClient(app)
    response = client.post("/ingest")

    assert response.status_code == 200
    assert response.json() == {"ingested_count": 0, "activities": []}
    assert captured["mode"] == "gmail"


def test_ingest_endpoint_does_not_return_known_mock_demo_names(tmp_path, monkeypatch) -> None:
    data_file = tmp_path / "activities.json"
    original_storage = routes.storage
    original_sheets = routes.sheets
    routes.storage = JSONStorageService(str(data_file))
    captured: dict[str, object] = {}

    class FakeState:
        def get_last_successful_ingestion_at(self) -> None:
            return None

        def set_last_successful_ingestion_at(self, value: datetime) -> None:
            captured["cursor_updated"] = value

    class EmptyGmailAdapter:
        last_fetch_succeeded = True

        def fetch_emails(self) -> list[RawEmail]:
            return []

    class KnownMockDemoAdapter:
        def fetch_emails(self) -> list[RawEmail]:
            return [
                RawEmail(
                    subject="Prof Maya Patel published a new paper on trustworthy ML systems",
                    sender="notifications-noreply@linkedin.com",
                    snippet="Mock demo publication",
                    body="https://www.linkedin.com/feed/update/urn:li:activity:known-mock",
                    received_at=datetime.now(timezone.utc),
                )
            ]

    class NoopSheets:
        def append_rows(self, rows: list[object]) -> None:
            return None

    def fake_build_ingestion_adapter(mode: str | None = None, received_after: datetime | None = None) -> object:
        captured["mode"] = mode
        if mode == "mock":
            return KnownMockDemoAdapter()
        return EmptyGmailAdapter()

    monkeypatch.setattr(routes.settings, "ingestion_mode", "mock")
    monkeypatch.setattr(routes, "ingestion_state", FakeState())
    monkeypatch.setattr(routes, "build_ingestion_adapter", fake_build_ingestion_adapter)
    monkeypatch.setattr(routes, "sheets", NoopSheets())

    try:
        client = TestClient(app)
        response = client.post("/ingest")

        assert response.status_code == 200
        payload_text = response.text
        assert response.json()["ingested_count"] == 0
        assert captured["mode"] == "gmail"
        assert "Maya Patel" not in payload_text
        assert "Omar Hassan" not in payload_text
        assert "known-mock" not in payload_text
    finally:
        routes.storage = original_storage
        routes.sheets = original_sheets


def test_gmail_ingestion_passes_cursor_and_advances_after_success(monkeypatch) -> None:
    cursor = datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc)
    captured: dict[str, object] = {}

    class FakeState:
        def __init__(self) -> None:
            self.updated_at: datetime | None = None

        def get_last_successful_ingestion_at(self) -> datetime:
            return cursor

        def set_last_successful_ingestion_at(self, value: datetime) -> None:
            self.updated_at = value

    class EmptyAdapter:
        def fetch_emails(self) -> list[RawEmail]:
            return []

    state = FakeState()

    def fake_build_ingestion_adapter(mode: str | None = None, received_after: datetime | None = None) -> EmptyAdapter:
        captured["mode"] = mode
        captured["received_after"] = received_after
        return EmptyAdapter()

    monkeypatch.setattr(routes, "ingestion_state", state)
    monkeypatch.setattr(routes, "build_ingestion_adapter", fake_build_ingestion_adapter)

    result = routes._run_ingestion(mode="gmail")

    assert result.ingested_count == 0
    assert captured == {"mode": "gmail", "received_after": cursor}
    assert state.updated_at is not None


def test_gmail_ingestion_does_not_advance_cursor_after_failure(monkeypatch) -> None:
    class FakeState:
        def __init__(self) -> None:
            self.updated_at: datetime | None = None

        def get_last_successful_ingestion_at(self) -> None:
            return None

        def set_last_successful_ingestion_at(self, value: datetime) -> None:
            self.updated_at = value

    class FailingAdapter:
        def fetch_emails(self) -> list[RawEmail]:
            raise RuntimeError("gmail failed")

    state = FakeState()

    monkeypatch.setattr(routes, "ingestion_state", state)
    monkeypatch.setattr(
        routes,
        "build_ingestion_adapter",
        lambda mode=None, received_after=None: FailingAdapter(),
    )

    with pytest.raises(RuntimeError, match="gmail failed"):
        routes._run_ingestion(mode="gmail")

    assert state.updated_at is None


def test_gmail_ingestion_does_not_advance_cursor_when_fetch_did_not_succeed(monkeypatch) -> None:
    class FakeState:
        def __init__(self) -> None:
            self.updated_at: datetime | None = None

        def get_last_successful_ingestion_at(self) -> None:
            return None

        def set_last_successful_ingestion_at(self, value: datetime) -> None:
            self.updated_at = value

    class FailedFetchAdapter:
        last_fetch_succeeded = False

        def fetch_emails(self) -> list[RawEmail]:
            return []

    state = FakeState()

    monkeypatch.setattr(routes, "ingestion_state", state)
    monkeypatch.setattr(
        routes,
        "build_ingestion_adapter",
        lambda mode=None, received_after=None: FailedFetchAdapter(),
    )

    result = routes._run_ingestion(mode="gmail")

    assert result.ingested_count == 0
    assert state.updated_at is None


def test_mock_ingestion_is_not_exposed_as_dashboard_api(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.post("/ingest/mock")

        assert response.status_code == 404
        assert routes.storage.list_all() == []
    finally:
        routes.storage = original_storage


def test_mock_ingestion_remains_available_to_tests(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        result = routes._run_ingestion(mode="mock")

        assert result.ingested_count >= 1
        first_activity = result.activities[0].model_dump(mode="json")
        assert set(["category", "ai_summary", "priority", "review_status"]).issubset(first_activity.keys())
        assert 1 <= first_activity["priority"] <= 5
        assert first_activity["review_status"] == ReviewStatus.pending.value
    finally:
        routes.storage = original_storage


def test_duplicate_ingestion_does_not_increase_stored_activity_count(tmp_path, monkeypatch) -> None:
    data_file = tmp_path / "activities.json"
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    class DuplicateAdapter:
        def fetch_emails(self) -> list[RawEmail]:
            return [
                RawEmail(
                    subject="Prof Alice Johnson published a paper",
                    sender="notifications-noreply@linkedin.com",
                    snippet="Publication update",
                    body="https://www.linkedin.com/feed/update/urn:li:activity:duplicate",
                    received_at=datetime.now(timezone.utc),
                )
            ]

    class NoopSheets:
        def append_rows(self, rows: list[object]) -> None:
            return None

    monkeypatch.setattr(routes, "build_ingestion_adapter", lambda mode=None, received_after=None: DuplicateAdapter())
    monkeypatch.setattr(routes, "sheets", NoopSheets())

    try:
        first = routes._run_ingestion(mode="mock")
        second = routes._run_ingestion(mode="mock")

        assert first.ingested_count == 1
        assert second.ingested_count == 0
        assert len(routes.storage.list_all()) == 1
    finally:
        routes.storage = original_storage


def test_duplicate_skipped_activities_are_not_sent_to_sheets(tmp_path, monkeypatch) -> None:
    data_file = tmp_path / "activities.json"
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))
    appended_rows: list[object] = []

    class DuplicateBatchAdapter:
        def fetch_emails(self) -> list[RawEmail]:
            received_at = datetime.now(timezone.utc)
            return [
                RawEmail(
                    subject="Prof Alice Johnson published a paper",
                    sender="notifications-noreply@linkedin.com",
                    snippet="Publication update",
                    body="https://www.linkedin.com/feed/update/urn:li:activity:duplicate",
                    received_at=received_at,
                ),
                RawEmail(
                    subject="Prof Alice Johnson published the same paper",
                    sender="notifications-noreply@linkedin.com",
                    snippet="Publication update",
                    body="https://www.linkedin.com/feed/update/urn:li:activity:duplicate",
                    received_at=received_at,
                ),
            ]

    class TrackingSheets:
        def append_rows(self, rows: list[object]) -> None:
            appended_rows.extend(rows)

    monkeypatch.setattr(routes, "build_ingestion_adapter", lambda mode=None, received_after=None: DuplicateBatchAdapter())
    monkeypatch.setattr(routes, "sheets", TrackingSheets())

    try:
        result = routes._run_ingestion(mode="mock")

        assert result.ingested_count == 1
        assert len(appended_rows) == 1
        assert len(routes.storage.list_all()) == 1
    finally:
        routes.storage = original_storage


def test_ub_cse_email_ingestion_uses_ub_cse_source_type(tmp_path, monkeypatch) -> None:
    data_file = tmp_path / "activities.json"
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    class UBCSEAdapter:
        def fetch_emails(self) -> list[RawEmail]:
            return [
                RawEmail(
                    subject="Research Matters: UB CSE faculty receive new funding",
                    sender="news@buffalo.edu",
                    snippet="University at Buffalo research update",
                    body=(
                        "University at Buffalo Department of Computer Science and Engineering "
                        "faculty received research funding for a new AI project."
                    ),
                    received_at=datetime.now(timezone.utc),
                )
            ]

    class NoopSheets:
        def append_rows(self, rows: list[object]) -> None:
            return None

    monkeypatch.setattr(routes, "build_ingestion_adapter", lambda mode=None, received_after=None: UBCSEAdapter())
    monkeypatch.setattr(routes, "sheets", NoopSheets())

    try:
        result = routes._run_ingestion(mode="gmail")

        assert result.ingested_count == 1
        assert result.activities[0].source_type == "ub_cse_email"
        assert result.activities[0].faculty_name is None
    finally:
        routes.storage = original_storage


def test_linkedin_email_ingestion_keeps_linkedin_source_type(tmp_path, monkeypatch) -> None:
    data_file = tmp_path / "activities.json"
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    class LinkedInAdapter:
        def fetch_emails(self) -> list[RawEmail]:
            return [
                RawEmail(
                    subject="Prof Maya Lee shared an update",
                    sender="LinkedIn <notifications-noreply@linkedin.com>",
                    snippet="Maya shared an update",
                    body="https://www.linkedin.com/feed/update/urn:li:activity:source-type",
                    received_at=datetime.now(timezone.utc),
                )
            ]

    class NoopSheets:
        def append_rows(self, rows: list[object]) -> None:
            return None

    monkeypatch.setattr(routes, "build_ingestion_adapter", lambda mode=None, received_after=None: LinkedInAdapter())
    monkeypatch.setattr(routes, "sheets", NoopSheets())

    try:
        result = routes._run_ingestion(mode="gmail")

        assert result.ingested_count == 1
        assert result.activities[0].source_type == "linkedin_email"
        assert result.activities[0].faculty_name == "Maya Lee"
    finally:
        routes.storage = original_storage


def test_list_activities_supports_filtering_sorting_and_pagination(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get(
            "/activities",
            params={
                "review_status": ReviewStatus.pending.value,
                "sort_by": "priority",
                "sort_order": "desc",
                "offset": 0,
                "limit": 1,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["review_status"] == ReviewStatus.pending.value
        assert payload[0]["id"] == "activity-3"
    finally:
        routes.storage = original_storage


def test_list_activity_page_returns_pagination_metadata(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get(
            "/activities/page",
            params={"sort_by": "detected_at", "sort_order": "desc", "limit": 2, "offset": 1},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 3
        assert payload["limit"] == 2
        assert payload["offset"] == 1
        assert [item["id"] for item in payload["items"]] == ["activity-3", "activity-1"]
    finally:
        routes.storage = original_storage


def test_list_activity_page_review_status_filter_still_works(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get(
            "/activities/page",
            params={"review_status": ReviewStatus.pending.value, "sort_by": "detected_at", "sort_order": "desc"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 2
        assert [item["review_status"] for item in payload["items"]] == [
            ReviewStatus.pending.value,
            ReviewStatus.pending.value,
        ]
    finally:
        routes.storage = original_storage


def test_list_activity_page_days_filter_returns_recent_items_only(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_dashboard_window_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get("/activities/page", params={"days": 30, "limit": 25, "offset": 0})

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 2
        assert [item["id"] for item in payload["items"]] == ["recent-pending", "recent-approved"]
    finally:
        routes.storage = original_storage


def test_list_activity_page_days_filter_excludes_old_rejected_items(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_dashboard_window_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get(
            "/activities/page",
            params={"review_status": ReviewStatus.rejected.value, "days": 30},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 0
        assert payload["items"] == []
    finally:
        routes.storage = original_storage


def test_list_activities_supports_category_filter_and_detected_at_sort(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get(
            "/activities",
            params={"category": ActivityCategory.talk_event.value, "sort_by": "detected_at", "sort_order": "desc"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["category"] == ActivityCategory.talk_event.value
        assert payload[0]["id"] == "activity-2"
    finally:
        routes.storage = original_storage


def test_list_pending_activities(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get("/activities", params={"review_status": ReviewStatus.pending.value})

        assert response.status_code == 200
        payload = response.json()
        assert [item["id"] for item in payload] == ["activity-3", "activity-1"]
        assert all(item["review_status"] == ReviewStatus.pending.value for item in payload)
    finally:
        routes.storage = original_storage


def test_approve_activity_by_id(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.post("/activities/activity-1/approve")

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == "activity-1"
        assert payload["review_status"] == ReviewStatus.approved.value
    finally:
        routes.storage = original_storage


def test_reject_activity_by_id(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.post("/activities/activity-3/reject")

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == "activity-3"
        assert payload["review_status"] == ReviewStatus.rejected.value
    finally:
        routes.storage = original_storage


def test_patch_activity_allows_approved_to_rejected(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-1", ReviewStatus.approved)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.patch(
            "/activities/activity-1",
            json={"review_status": ReviewStatus.rejected.value},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == "activity-1"
        assert payload["review_status"] == ReviewStatus.rejected.value
    finally:
        routes.storage = original_storage


def test_patch_activity_allows_rejected_to_approved(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-3", ReviewStatus.rejected)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.patch(
            "/activities/activity-3",
            json={"review_status": ReviewStatus.approved.value},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == "activity-3"
        assert payload["review_status"] == ReviewStatus.approved.value
    finally:
        routes.storage = original_storage


def test_batch_approve_updates_multiple_pending_items(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.patch(
            "/activities/batch",
            json={
                "ids": ["activity-1", "activity-3"],
                "review_status": ReviewStatus.approved.value,
            },
        )

        assert response.status_code == 200
        assert response.json() == {"updated_count": 2}
        approved_ids = [
            item["id"]
            for item in client.get(
                "/activities",
                params={"review_status": ReviewStatus.approved.value},
            ).json()
        ]
        assert approved_ids == ["activity-3", "activity-1"]
    finally:
        routes.storage = original_storage


def test_batch_reject_updates_multiple_approved_items(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-1", ReviewStatus.approved)
    storage.update_review_status("activity-3", ReviewStatus.approved)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.patch(
            "/activities/batch",
            json={
                "ids": ["activity-1", "activity-3"],
                "review_status": ReviewStatus.rejected.value,
            },
        )

        assert response.status_code == 200
        assert response.json() == {"updated_count": 2}
        rejected_ids = [
            item["id"]
            for item in client.get(
                "/activities",
                params={"review_status": ReviewStatus.rejected.value},
            ).json()
        ]
        assert rejected_ids == ["activity-3", "activity-1"]
    finally:
        routes.storage = original_storage


def test_batch_update_ignores_nonexistent_ids(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.patch(
            "/activities/batch",
            json={
                "ids": ["activity-1", "missing-activity"],
                "review_status": ReviewStatus.approved.value,
            },
        )

        assert response.status_code == 200
        assert response.json() == {"updated_count": 1}
        assert client.get("/activities/missing-activity").status_code == 404
    finally:
        routes.storage = original_storage


def test_delete_rejected_activity_removes_it(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-3", ReviewStatus.rejected)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.delete("/activities/activity-3")

        assert response.status_code == 200
        assert response.json() == {"deleted": True}
        assert client.get("/activities/activity-3").status_code == 404
    finally:
        routes.storage = original_storage


def test_delete_approved_activity_does_not_remove_it(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-1", ReviewStatus.approved)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.delete("/activities/activity-1")

        assert response.status_code == 200
        assert response.json() == {"deleted": False}
        assert client.get("/activities/activity-1").status_code == 200
    finally:
        routes.storage = original_storage


def test_delete_pending_activity_does_not_remove_it(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.delete("/activities/activity-1")

        assert response.status_code == 200
        assert response.json() == {"deleted": False}
        assert client.get("/activities/activity-1").status_code == 200
    finally:
        routes.storage = original_storage


def test_batch_delete_removes_multiple_rejected_items(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-1", ReviewStatus.rejected)
    storage.update_review_status("activity-3", ReviewStatus.rejected)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.request(
            "DELETE",
            "/activities/batch",
            json={"ids": ["activity-1", "activity-3"]},
        )

        assert response.status_code == 200
        assert response.json() == {"deleted_count": 2}
        assert client.get("/activities/activity-1").status_code == 404
        assert client.get("/activities/activity-3").status_code == 404
    finally:
        routes.storage = original_storage


def test_batch_delete_ignores_nonexistent_ids(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-3", ReviewStatus.rejected)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.request(
            "DELETE",
            "/activities/batch",
            json={"ids": ["activity-3", "missing-activity"]},
        )

        assert response.status_code == 200
        assert response.json() == {"deleted_count": 1}
        assert client.get("/activities/activity-3").status_code == 404
    finally:
        routes.storage = original_storage


def test_batch_delete_ignores_approved_and_pending_items(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-2", ReviewStatus.approved)
    storage.update_review_status("activity-3", ReviewStatus.rejected)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.request(
            "DELETE",
            "/activities/batch",
            json={"ids": ["activity-1", "activity-2", "activity-3"]},
        )

        assert response.status_code == 200
        assert response.json() == {"deleted_count": 1}
        assert client.get("/activities/activity-1").status_code == 200
        assert client.get("/activities/activity-2").status_code == 200
        assert client.get("/activities/activity-3").status_code == 404
    finally:
        routes.storage = original_storage


def test_approved_activity_no_longer_appears_pending(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        approve_response = client.post("/activities/activity-1/approve")
        pending_response = client.get("/activities", params={"review_status": ReviewStatus.pending.value})

        assert approve_response.status_code == 200
        assert pending_response.status_code == 200
        pending_ids = [item["id"] for item in pending_response.json()]
        assert pending_ids == ["activity-3"]
    finally:
        routes.storage = original_storage


def test_list_approved_activities_endpoint_excludes_pending_and_rejected(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    storage = JSONStorageService(str(data_file))
    storage.update_review_status("activity-2", ReviewStatus.approved)
    storage.update_review_status("activity-3", ReviewStatus.rejected)
    original_storage = routes.storage
    routes.storage = storage

    try:
        client = TestClient(app)
        response = client.get("/activities/approved")

        assert response.status_code == 200
        payload = response.json()
        assert [item["id"] for item in payload] == ["activity-2"]
        assert all(item["review_status"] == ReviewStatus.approved.value for item in payload)
    finally:
        routes.storage = original_storage


def test_public_activities_returns_approved_only_in_manual_mode(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage, original_mode_store = _configure_public_activity_test(data_file, mode_file)

    try:
        client = TestClient(app)
        mode_response = client.put("/activities/public/mode", json={"mode": "manual"})
        response = client.get("/activities/public")

        assert mode_response.status_code == 200
        assert mode_response.json() == {"mode": "manual"}
        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == ["public-approved"]
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store


def test_public_activities_returns_approved_and_pending_in_auto_mode(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage, original_mode_store = _configure_public_activity_test(data_file, mode_file)

    try:
        client = TestClient(app)
        mode_response = client.put("/activities/public/mode", json={"mode": "auto"})
        response = client.get("/activities/public")

        assert mode_response.status_code == 200
        assert mode_response.json() == {"mode": "auto"}
        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == ["public-pending", "public-approved"]
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store


def test_public_activities_never_returns_rejected_items(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage, original_mode_store = _configure_public_activity_test(data_file, mode_file)

    try:
        client = TestClient(app)
        client.put("/activities/public/mode", json={"mode": "auto"})
        payload = client.get("/activities/public").json()

        assert "public-rejected" not in [item["id"] for item in payload]
        assert all(item["review_status"] != ReviewStatus.rejected.value for item in payload)
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store


def test_digest_preview_returns_plain_text_digest(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get("/digest/preview", params={"review_status": ReviewStatus.pending.value})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "# Weekly Activity Digest" in response.text
        assert "Review status: pending" in response.text
        assert "Workshop event." not in response.text
    finally:
        routes.storage = original_storage


def test_digest_returns_grouped_json_structure(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get("/digest", params={"review_status": ReviewStatus.pending.value, "max_items_per_category": 1})

        assert response.status_code == 200
        payload = response.json()
        assert payload["review_status"] == ReviewStatus.pending.value
        assert payload["total_items"] == 2
        assert len(payload["sections"]) == 2
        assert all("category" in section and "items" in section for section in payload["sections"])
        assert all(len(section["items"]) <= 1 for section in payload["sections"])
    finally:
        routes.storage = original_storage


def test_digest_markdown_export_returns_text_without_changing_preview(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        export_response = client.get(
            "/digest/export/markdown",
            params={"review_status": ReviewStatus.pending.value, "include_section_totals": "true", "max_items_per_category": 1},
        )
        preview_response = client.get("/digest/preview", params={"review_status": ReviewStatus.pending.value})

        assert export_response.status_code == 200
        assert export_response.headers["content-type"].startswith("text/plain")
        assert "## Publication (1)" in export_response.text or "## Award (1)" in export_response.text
        assert export_response.text.count("- [P") == 2
        assert "# Weekly Activity Digest" in preview_response.text
    finally:
        routes.storage = original_storage
