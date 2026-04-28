import base64
import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.schemas import ActivityCategory, ReviewStatus
from app.services.public_fetch_mode import PublicFetchModeStore
from app.services.storage import JSONStorageService


def _basic_auth_headers(password: str, username: str = "admin") -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


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
    ]
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def test_public_routes_remain_open_and_admin_root_requires_auth(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage = routes.storage
    original_mode_store = routes.public_fetch_mode_store
    original_password = routes.settings.admin_password
    routes.storage = JSONStorageService(str(data_file))
    routes.public_fetch_mode_store = PublicFetchModeStore(str(mode_file))
    routes.settings.admin_password = "secret-admin"

    try:
        client = TestClient(app)

        root_admin = client.get("/")
        assert root_admin.status_code == 401

        root_public = client.get("/?public=1")
        assert root_public.status_code == 200
        assert "text/html" in root_public.headers["content-type"]

        public_activities = client.get("/activities/public")
        assert public_activities.status_code == 200

        public_mode = client.get("/activities/public/mode")
        assert public_mode.status_code == 200

        static_js = client.get("/static/dashboard.js")
        assert static_js.status_code == 200
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store
        routes.settings.admin_password = original_password


def test_protected_routes_reject_unauthenticated_requests(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage = routes.storage
    original_mode_store = routes.public_fetch_mode_store
    original_password = routes.settings.admin_password
    routes.storage = JSONStorageService(str(data_file))
    routes.public_fetch_mode_store = PublicFetchModeStore(str(mode_file))
    routes.settings.admin_password = "secret-admin"

    try:
        client = TestClient(app)

        assert client.post("/ingest").status_code == 401
        assert client.get("/activities/page").status_code == 401
        assert client.patch("/activities/public-pending", json={"review_status": "approved"}).status_code == 401
        assert client.patch("/activities/batch", json={"ids": ["public-pending"], "review_status": "approved"}).status_code == 401
        assert client.delete("/activities/public-pending").status_code == 401
        assert client.request("DELETE", "/activities/batch", json={"ids": ["public-pending"]}).status_code == 401
        assert client.put("/activities/public/mode", json={"mode": "auto"}).status_code == 401
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store
        routes.settings.admin_password = original_password


def test_protected_routes_allow_valid_admin_auth(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage = routes.storage
    original_mode_store = routes.public_fetch_mode_store
    original_password = routes.settings.admin_password
    routes.storage = JSONStorageService(str(data_file))
    routes.public_fetch_mode_store = PublicFetchModeStore(str(mode_file))
    routes.settings.admin_password = "secret-admin"

    try:
        client = TestClient(app)
        headers = _basic_auth_headers("secret-admin")

        assert client.get("/", headers=headers).status_code == 200
        assert client.get("/activities/page", headers=headers).status_code == 200
        assert client.put("/activities/public/mode", json={"mode": "auto"}, headers=headers).status_code == 200
        assert client.get("/activities/public/mode").status_code == 200
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store
        routes.settings.admin_password = original_password


def test_protected_routes_fail_closed_when_admin_password_unset() -> None:
    original_password = routes.settings.admin_password
    routes.settings.admin_password = ""

    try:
        client = TestClient(app)
        response = client.get("/activities/page", headers=_basic_auth_headers("anything"))
        assert response.status_code == 500
        assert response.json()["detail"] == "ADMIN_PASSWORD is not configured."
    finally:
        routes.settings.admin_password = original_password
