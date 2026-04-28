import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.schemas import ActivityCategory, ReviewStatus
from app.services.public_fetch_mode import PublicFetchModeStore
from app.services.storage import JSONStorageService


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


def _set_admin_config() -> tuple[str, str, str]:
    original_username = routes.settings.admin_username
    original_password = routes.settings.admin_password
    original_secret = routes.settings.admin_session_secret
    routes.settings.admin_username = "admin"
    routes.settings.admin_password = "secret-admin"
    routes.settings.admin_session_secret = "test-session-secret"
    return original_username, original_password, original_secret


def _restore_admin_config(original: tuple[str, str, str]) -> None:
    routes.settings.admin_username, routes.settings.admin_password, routes.settings.admin_session_secret = original


def test_login_page_renders_without_auth() -> None:
    original = _set_admin_config()
    try:
        client = TestClient(app)
        response = client.get("/login")
        assert response.status_code == 200
        assert "Admin Login" in response.text
        assert "<form method=\"post\" action=\"/login\"" in response.text
    finally:
        _restore_admin_config(original)


def test_login_valid_credentials_sets_session_cookie() -> None:
    original = _set_admin_config()
    try:
        client = TestClient(app, follow_redirects=False)
        response = client.post("/login", data={"username": "admin", "password": "secret-admin"})

        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert "cse_admin_session" in response.cookies
    finally:
        _restore_admin_config(original)


def test_login_invalid_credentials_does_not_authenticate() -> None:
    original = _set_admin_config()
    try:
        client = TestClient(app)
        response = client.post("/login", data={"username": "admin", "password": "wrong"})

        assert response.status_code == 401
        assert "Invalid username or password." in response.text
        assert "cse_admin_session" not in response.cookies
    finally:
        _restore_admin_config(original)


def test_public_routes_remain_open_and_admin_root_requires_session(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage = routes.storage
    original_mode_store = routes.public_fetch_mode_store
    original_admin = _set_admin_config()
    routes.storage = JSONStorageService(str(data_file))
    routes.public_fetch_mode_store = PublicFetchModeStore(str(mode_file))

    try:
        client = TestClient(app, follow_redirects=False)

        root_admin = client.get("/")
        assert root_admin.status_code == 303
        assert root_admin.headers["location"] == "/login"

        root_public = client.get("/?public=1")
        assert root_public.status_code == 200

        public_activities = client.get("/activities/public")
        assert public_activities.status_code == 200

        public_mode = client.get("/activities/public/mode")
        assert public_mode.status_code == 200
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store
        _restore_admin_config(original_admin)


def test_protected_routes_reject_without_session(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage = routes.storage
    original_mode_store = routes.public_fetch_mode_store
    original_admin = _set_admin_config()
    routes.storage = JSONStorageService(str(data_file))
    routes.public_fetch_mode_store = PublicFetchModeStore(str(mode_file))

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
        _restore_admin_config(original_admin)


def test_protected_routes_allow_valid_session_and_logout_clears_it(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    mode_file = tmp_path / "public_fetch_mode.json"
    _seed_public_activity_file(str(data_file))
    original_storage = routes.storage
    original_mode_store = routes.public_fetch_mode_store
    original_admin = _set_admin_config()
    routes.storage = JSONStorageService(str(data_file))
    routes.public_fetch_mode_store = PublicFetchModeStore(str(mode_file))

    try:
        client = TestClient(app, follow_redirects=False)
        login = client.post("/login", data={"username": "admin", "password": "secret-admin"})
        assert login.status_code == 303

        assert client.get("/").status_code == 200
        assert client.get("/activities/page").status_code == 200
        assert client.put("/activities/public/mode", json={"mode": "auto"}).status_code == 200
        assert client.get("/activities/public/mode").status_code == 200

        logout = client.post("/logout")
        assert logout.status_code == 303
        assert logout.headers["location"] == "/login"
        assert client.get("/activities/page").status_code == 401
    finally:
        routes.storage = original_storage
        routes.public_fetch_mode_store = original_mode_store
        _restore_admin_config(original_admin)


def test_protected_routes_fail_closed_when_admin_config_is_unset() -> None:
    original = (
        routes.settings.admin_username,
        routes.settings.admin_password,
        routes.settings.admin_session_secret,
    )
    routes.settings.admin_username = ""
    routes.settings.admin_password = ""
    routes.settings.admin_session_secret = ""

    try:
        client = TestClient(app, follow_redirects=False)
        admin_dashboard = client.get("/")
        assert admin_dashboard.status_code == 303
        assert admin_dashboard.headers["location"] == "/login"

        protected_api = client.get("/activities/page")
        assert protected_api.status_code == 500
        assert protected_api.json()["detail"] == "Admin auth is not configured."

        login = client.post("/login", data={"username": "admin", "password": "secret-admin"})
        assert login.status_code == 500
        assert "Admin auth is not configured." in login.text
    finally:
        routes.settings.admin_username, routes.settings.admin_password, routes.settings.admin_session_secret = original
