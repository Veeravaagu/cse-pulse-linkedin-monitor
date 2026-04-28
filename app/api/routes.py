import hashlib
import hmac
import secrets
from urllib.parse import parse_qs
from pathlib import Path
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, Response
from pydantic import BaseModel

from app.config import settings
from app.models.schemas import ActivityCategory, ActivityRecord, IngestResponse, ReviewStatus
from app.services.digest_service import DigestService
from app.services.enrichment import build_enrichment_processor
from app.services.gmail_parser import GmailParser
from app.services.ingestion import build_ingestion_adapter
from app.services.ingestion.gmail_api_adapter import is_likely_linkedin_email, is_likely_ub_cse_activity_email
from app.services.ingestion_state import IngestionStateStore
from app.services.public_fetch_mode import PublicFetchMode, PublicFetchModeStore
from app.services.sheets_client import GoogleSheetsClient
from app.services.storage import JSONStorageService
from app.services.storage_base import ActivityStorage

router = APIRouter()
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
ADMIN_SESSION_COOKIE = "cse_admin_session"
CSRF_COOKIE = "cse_csrf_token"
ADMIN_SESSION_MAX_AGE_SECONDS = 60 * 60 * 12


class PublicFetchModePayload(BaseModel):
    mode: PublicFetchMode


class ActivityReviewStatusPayload(BaseModel):
    review_status: Literal["approved", "rejected", "pending"]


class BatchActivityReviewStatusPayload(BaseModel):
    ids: list[str]
    review_status: Literal["approved", "rejected"]


class BatchActivityDeletePayload(BaseModel):
    ids: list[str]


parser = GmailParser()
storage: ActivityStorage = JSONStorageService(settings.data_file)
ingestion_state = IngestionStateStore(settings.ingestion_state_file)
public_fetch_mode_store = PublicFetchModeStore(settings.public_fetch_mode_file)
sheets = GoogleSheetsClient(
    settings.google_sheets_id,
    settings.google_sheets_worksheet,
    enabled=settings.google_sheets_enabled,
    credentials_path=settings.google_service_account_path or settings.google_service_account_json,
)


def _validate_admin_config() -> None:
    if not settings.admin_username or not settings.admin_password:
        raise HTTPException(status_code=500, detail="Admin auth is not configured.")
    if not settings.admin_session_secret:
        raise HTTPException(status_code=500, detail="ADMIN_SESSION_SECRET is not configured.")


def _build_session_signature(username: str, issued_at: int, csrf_token: str) -> str:
    payload = f"{username}:{issued_at}:{csrf_token}".encode("utf-8")
    secret = settings.admin_session_secret.encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def _build_session_cookie(username: str, csrf_token: str) -> str:
    issued_at = int(datetime.now(timezone.utc).timestamp())
    signature = _build_session_signature(username, issued_at, csrf_token)
    return f"{username}:{issued_at}:{csrf_token}:{signature}"


def _parse_session_cookie(cookie_value: str | None) -> tuple[str, int, str] | None:
    if not cookie_value:
        return None
    parts = cookie_value.split(":")
    if len(parts) != 4:
        return None

    username, issued_raw, csrf_token, signature = parts
    if username != settings.admin_username:
        return None
    if not issued_raw.isdigit():
        return None

    issued_at = int(issued_raw)
    now = int(datetime.now(timezone.utc).timestamp())
    if issued_at > now or now - issued_at > ADMIN_SESSION_MAX_AGE_SECONDS:
        return None

    expected = _build_session_signature(username, issued_at, csrf_token)
    if not hmac.compare_digest(signature, expected):
        return None
    return username, issued_at, csrf_token


def _is_valid_session_cookie(cookie_value: str | None) -> bool:
    return _parse_session_cookie(cookie_value) is not None


def _is_admin_authenticated(request: Request) -> bool:
    try:
        _validate_admin_config()
    except HTTPException:
        return False
    return _is_valid_session_cookie(request.cookies.get(ADMIN_SESSION_COOKIE))


def require_admin(request: Request) -> None:
    _validate_admin_config()
    if _is_valid_session_cookie(request.cookies.get(ADMIN_SESSION_COOKIE)):
        return
    raise HTTPException(status_code=401, detail="Admin authentication required.")


def require_admin_dashboard(request: Request) -> None:
    _validate_admin_config()
    if request.query_params.get("public") == "1":
        return
    if _is_valid_session_cookie(request.cookies.get(ADMIN_SESSION_COOKIE)):
        return
    raise HTTPException(status_code=401, detail="Admin authentication required.")


def require_csrf(request: Request) -> None:
    session = _parse_session_cookie(request.cookies.get(ADMIN_SESSION_COOKIE))
    if session is None:
        raise HTTPException(status_code=401, detail="Admin authentication required.")
    _, _, session_csrf = session
    cookie_csrf = request.cookies.get(CSRF_COOKIE, "")
    header_csrf = request.headers.get("X-CSRF-Token", "")
    if not header_csrf or not cookie_csrf:
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid.")
    if not hmac.compare_digest(header_csrf, cookie_csrf):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid.")
    if not hmac.compare_digest(header_csrf, session_csrf):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid.")


def _render_login_page(error: str = "", status_code: int = 200) -> HTMLResponse:
    error_markup = f'<p style="color:#b42318;margin:0 0 12px 0;">{error}</p>' if error else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Admin Login</title>
  </head>
  <body style="font-family: sans-serif; background: #f6f7fb; margin: 0; padding: 32px;">
    <main style="max-width: 360px; margin: 0 auto; background: #fff; border: 1px solid #d8dce6; border-radius: 8px; padding: 20px;">
      <h1 style="margin: 0 0 10px 0; font-size: 22px;">Admin Login</h1>
      <p style="margin: 0 0 16px 0; color: #475467;">Sign in to access the admin dashboard.</p>
      {error_markup}
      <form method="post" action="/login" style="display: grid; gap: 12px;">
        <label style="display:grid; gap:6px;">
          <span>Username</span>
          <input type="text" name="username" required />
        </label>
        <label style="display:grid; gap:6px;">
          <span>Password</span>
          <input type="password" name="password" required />
        </label>
        <button type="submit">Sign in</button>
      </form>
    </main>
  </body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


@router.get("/login", include_in_schema=False)
def login_page(request: Request) -> Response:
    if _is_admin_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    return _render_login_page()


@router.post("/login", include_in_schema=False)
async def login_submit(request: Request) -> Response:
    body = (await request.body()).decode("utf-8", errors="ignore")
    parsed = parse_qs(body)
    username = (parsed.get("username") or [""])[0]
    password = (parsed.get("password") or [""])[0]

    try:
        _validate_admin_config()
    except HTTPException as exc:
        return _render_login_page(error=exc.detail, status_code=500)

    valid_username = secrets.compare_digest(username, settings.admin_username)
    valid_password = secrets.compare_digest(password, settings.admin_password)
    if not (valid_username and valid_password):
        return _render_login_page(error="Invalid username or password.", status_code=401)

    csrf_token = secrets.token_urlsafe(32)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=_build_session_cookie(username=settings.admin_username, csrf_token=csrf_token),
        httponly=True,
        samesite="lax",
        max_age=ADMIN_SESSION_MAX_AGE_SECONDS,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        httponly=False,
        samesite="lax",
        max_age=ADMIN_SESSION_MAX_AGE_SECONDS,
        path="/",
    )
    return response


@router.post("/logout", include_in_schema=False)
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=ADMIN_SESSION_COOKIE, path="/")
    response.delete_cookie(key=CSRF_COOKIE, path="/")
    return response


@router.get("/health")
def health() -> dict[str, object]:
    activities = storage.list_all()
    return {
        "status": "ok",
        "service": settings.app_name,
        "storage": "ok",
        "activity_count": len(activities),
    }


@router.get("/", include_in_schema=False)
def dashboard(request: Request) -> Response:
    """Serve the small demo dashboard."""

    if request.query_params.get("public") == "1":
        return FileResponse(STATIC_DIR / "dashboard.html")
    try:
        require_admin_dashboard(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse(STATIC_DIR / "dashboard.html")


def _build_digest_service() -> DigestService:
    """Build the digest service from the current storage dependency."""

    return DigestService(storage)


@router.get("/digest/preview", response_class=PlainTextResponse)
def digest_preview(
    start_date: date | None = None,
    end_date: date | None = None,
    review_status: ReviewStatus | None = None,
    _: None = Depends(require_admin),
) -> str:
    return _build_digest_service().generate_preview(
        start_date=start_date,
        end_date=end_date,
        review_status=review_status,
    )


@router.get("/digest")
def digest(
    start_date: date | None = None,
    end_date: date | None = None,
    review_status: ReviewStatus | None = None,
    max_items_per_category: int | None = Query(default=None, ge=1),
    _: None = Depends(require_admin),
) -> dict[str, object]:
    return _build_digest_service().generate_structured(
        start_date=start_date,
        end_date=end_date,
        review_status=review_status,
        max_items_per_category=max_items_per_category,
    )


@router.get("/digest/export/markdown", response_class=PlainTextResponse)
def digest_export_markdown(
    start_date: date | None = None,
    end_date: date | None = None,
    review_status: ReviewStatus | None = None,
    max_items_per_category: int | None = Query(default=None, ge=1),
    include_section_totals: bool = False,
    summary_max_length: int | None = Query(default=None, ge=1),
    _: None = Depends(require_admin),
) -> str:
    return _build_digest_service().generate_markdown_export(
        start_date=start_date,
        end_date=end_date,
        review_status=review_status,
        max_items_per_category=max_items_per_category,
        include_section_totals=include_section_totals,
        summary_max_length=summary_max_length,
    )


@router.get("/activities", response_model=list[ActivityRecord])
def list_activities(
    category: ActivityCategory | None = None,
    review_status: ReviewStatus | None = None,
    sort_by: Literal["detected_at", "priority"] = "detected_at",
    sort_order: Literal["asc", "desc"] = "desc",
    offset: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    _: None = Depends(require_admin),
) -> list[ActivityRecord]:
    return storage.list_activities(
        category=category,
        review_status=review_status,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )


@router.get("/activities/page")
def list_activity_page(
    category: ActivityCategory | None = None,
    review_status: ReviewStatus | None = None,
    sort_by: Literal["detected_at", "priority"] = "detected_at",
    sort_order: Literal["asc", "desc"] = "desc",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1),
    days: int | None = Query(default=None, ge=1),
    _: None = Depends(require_admin),
) -> dict[str, object]:
    filtered = storage.list_activities(
        category=category,
        review_status=review_status,
        sort_by=sort_by,
        sort_order=sort_order,
        days=days,
    )
    items = storage.list_activities(
        category=category,
        review_status=review_status,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
        days=days,
    )

    return {
        "items": items,
        "total": len(filtered),
        "limit": limit,
        "offset": offset,
    }


@router.get("/activities/high-priority", response_model=list[ActivityRecord])
def high_priority(_: None = Depends(require_admin)) -> list[ActivityRecord]:
    return storage.list_high_priority(threshold=4)


@router.get("/activities/approved", response_model=list[ActivityRecord])
def list_approved_activities(_: None = Depends(require_admin)) -> list[ActivityRecord]:
    return storage.list_activities(review_status=ReviewStatus.approved)


@router.get("/activities/public", response_model=list[ActivityRecord])
def list_public_activities() -> list[ActivityRecord]:
    mode = public_fetch_mode_store.get_mode()
    allowed_statuses = {ReviewStatus.approved}
    if mode == "auto":
        allowed_statuses.add(ReviewStatus.pending)

    return [
        item
        for item in storage.list_activities(sort_by="detected_at", sort_order="desc")
        if item.review_status in allowed_statuses
    ]


@router.get("/activities/public/mode")
def get_public_fetch_mode() -> dict[str, PublicFetchMode]:
    return {"mode": public_fetch_mode_store.get_mode()}


@router.put("/activities/public/mode")
def update_public_fetch_mode(
    payload: PublicFetchModePayload,
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> dict[str, PublicFetchMode]:
    return {"mode": public_fetch_mode_store.set_mode(payload.mode)}


@router.patch("/activities/batch")
def batch_update_activity_review_status(
    payload: BatchActivityReviewStatusPayload,
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> dict[str, int]:
    review_status = ReviewStatus(payload.review_status)
    updated_count = 0

    for activity_id in payload.ids:
        if storage.update_review_status(activity_id, review_status):
            updated_count += 1

    return {"updated_count": updated_count}


@router.delete("/activities/batch")
def batch_delete_rejected_activities(
    payload: BatchActivityDeletePayload,
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> dict[str, int]:
    return {"deleted_count": storage.delete_rejected_many(payload.ids)}


@router.get("/activities/{activity_id}", response_model=ActivityRecord)
def get_activity(activity_id: str, _: None = Depends(require_admin)) -> ActivityRecord:
    record = storage.get_by_id(activity_id)
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


@router.patch("/activities/{activity_id}", response_model=ActivityRecord)
def update_activity_review_status(
    activity_id: str,
    payload: ActivityReviewStatusPayload,
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> ActivityRecord:
    record = storage.update_review_status(activity_id, ReviewStatus(payload.review_status))
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


@router.delete("/activities/{activity_id}")
def delete_rejected_activity(
    activity_id: str,
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> dict[str, bool]:
    return {"deleted": storage.delete_rejected(activity_id)}


@router.post("/activities/{activity_id}/approve", response_model=ActivityRecord)
def approve_activity(
    activity_id: str,
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> ActivityRecord:
    record = storage.update_review_status(activity_id, ReviewStatus.approved)
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


@router.post("/activities/{activity_id}/reject", response_model=ActivityRecord)
def reject_activity(
    activity_id: str,
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> ActivityRecord:
    record = storage.update_review_status(activity_id, ReviewStatus.rejected)
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


def _run_ingestion(mode: str | None = None) -> IngestResponse:
    """Shared ingestion flow for the selected adapter mode.

    Beginner note:
    1) adapter fetches raw emails
    2) parser extracts structured fields
    3) AI adds summary/category/priority
    4) storage persists final rows
    """

    selected_mode = (mode or settings.ingestion_mode).strip().lower()
    received_after = (
        ingestion_state.get_last_successful_ingestion_at()
        if selected_mode == "gmail"
        else None
    )
    adapter = build_ingestion_adapter(mode, received_after=received_after)
    enrichment_processor = build_enrichment_processor()
    raw_emails = adapter.fetch_emails()
    created: list[ActivityRecord] = []

    for raw in raw_emails:
        parsed = parser.parse(raw)
        if is_likely_ub_cse_activity_email(raw) and not is_likely_linkedin_email(raw):
            parsed.source_type = "ub_cse_email"
        if parsed.source_url and storage.exists_by_source_url(parsed.source_url):
            continue

        enriched = enrichment_processor.enrich(parsed)
        record = storage.create(parsed, enriched)
        created.append(record)

    if created:
        sheets.append_rows(created)

    result = IngestResponse(ingested_count=len(created), activities=created)
    if selected_mode == "gmail" and getattr(adapter, "last_fetch_succeeded", True):
        ingestion_state.set_last_successful_ingestion_at(datetime.now(timezone.utc))
    return result


@router.post("/ingest", response_model=IngestResponse)
def ingest_emails(
    _: None = Depends(require_admin),
    __: None = Depends(require_csrf),
) -> IngestResponse:
    return _run_ingestion(mode="gmail")
