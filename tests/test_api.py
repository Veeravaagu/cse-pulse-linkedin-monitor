import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.schemas import ActivityCategory, ReviewStatus
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
            "category": ActivityCategory.event.value,
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


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_dashboard_page_loads() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "CSE Pulse Operations Dashboard" in response.text
    assert "Activity Inbox" in response.text


def test_ingest_mock() -> None:
    client = TestClient(app)
    response = client.post("/ingest/mock")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ingested_count"] >= 1
    first_activity = payload["activities"][0]
    assert set(["category", "ai_summary", "priority", "review_status"]).issubset(first_activity.keys())
    assert 1 <= first_activity["priority"] <= 5
    assert first_activity["review_status"] == ReviewStatus.pending.value


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


def test_list_activities_supports_category_filter_and_detected_at_sort(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_activity_file(str(data_file))
    original_storage = routes.storage
    routes.storage = JSONStorageService(str(data_file))

    try:
        client = TestClient(app)
        response = client.get(
            "/activities",
            params={"category": ActivityCategory.event.value, "sort_by": "detected_at", "sort_order": "desc"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["category"] == ActivityCategory.event.value
        assert payload[0]["id"] == "activity-2"
    finally:
        routes.storage = original_storage


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
