from pathlib import Path
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
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


class PublicFetchModePayload(BaseModel):
    mode: PublicFetchMode


class ActivityReviewStatusPayload(BaseModel):
    review_status: Literal["approved", "rejected", "pending"]


class BatchActivityReviewStatusPayload(BaseModel):
    ids: list[str]
    review_status: Literal["approved", "rejected"]


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
def dashboard() -> FileResponse:
    """Serve the small demo dashboard."""

    return FileResponse(STATIC_DIR / "dashboard.html")


def _build_digest_service() -> DigestService:
    """Build the digest service from the current storage dependency."""

    return DigestService(storage)


@router.get("/digest/preview", response_class=PlainTextResponse)
def digest_preview(
    start_date: date | None = None,
    end_date: date | None = None,
    review_status: ReviewStatus | None = None,
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
def high_priority() -> list[ActivityRecord]:
    return storage.list_high_priority(threshold=4)


@router.get("/activities/approved", response_model=list[ActivityRecord])
def list_approved_activities() -> list[ActivityRecord]:
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
def update_public_fetch_mode(payload: PublicFetchModePayload) -> dict[str, PublicFetchMode]:
    return {"mode": public_fetch_mode_store.set_mode(payload.mode)}


@router.patch("/activities/batch")
def batch_update_activity_review_status(payload: BatchActivityReviewStatusPayload) -> dict[str, int]:
    review_status = ReviewStatus(payload.review_status)
    updated_count = 0

    for activity_id in payload.ids:
        if storage.update_review_status(activity_id, review_status):
            updated_count += 1

    return {"updated_count": updated_count}


@router.get("/activities/{activity_id}", response_model=ActivityRecord)
def get_activity(activity_id: str) -> ActivityRecord:
    record = storage.get_by_id(activity_id)
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


@router.patch("/activities/{activity_id}", response_model=ActivityRecord)
def update_activity_review_status(
    activity_id: str,
    payload: ActivityReviewStatusPayload,
) -> ActivityRecord:
    record = storage.update_review_status(activity_id, ReviewStatus(payload.review_status))
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


@router.post("/activities/{activity_id}/approve", response_model=ActivityRecord)
def approve_activity(activity_id: str) -> ActivityRecord:
    record = storage.update_review_status(activity_id, ReviewStatus.approved)
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


@router.post("/activities/{activity_id}/reject", response_model=ActivityRecord)
def reject_activity(activity_id: str) -> ActivityRecord:
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
def ingest_emails() -> IngestResponse:
    return _run_ingestion(mode="gmail")
