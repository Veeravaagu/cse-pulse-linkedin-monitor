from pathlib import Path
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse

from app.config import settings
from app.models.schemas import ActivityCategory, ActivityRecord, IngestResponse, ReviewStatus
from app.services.digest_service import DigestService
from app.services.enrichment import build_enrichment_processor
from app.services.gmail_parser import GmailParser
from app.services.ingestion import build_ingestion_adapter
from app.services.sheets_client import GoogleSheetsClient
from app.services.storage import JSONStorageService
from app.services.storage_base import ActivityStorage

router = APIRouter()
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

parser = GmailParser()
storage: ActivityStorage = JSONStorageService(settings.data_file)
sheets = GoogleSheetsClient(
    settings.google_sheets_id,
    settings.google_sheets_worksheet,
    enabled=settings.google_sheets_enabled,
    credentials_path=settings.google_service_account_path or settings.google_service_account_json,
)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


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


@router.get("/activities/high-priority", response_model=list[ActivityRecord])
def high_priority() -> list[ActivityRecord]:
    return storage.list_high_priority(threshold=4)


@router.get("/activities/{activity_id}", response_model=ActivityRecord)
def get_activity(activity_id: str) -> ActivityRecord:
    record = storage.get_by_id(activity_id)
    if not record:
        raise HTTPException(status_code=404, detail="Activity not found")
    return record


def _run_ingestion(mode: str | None = None) -> IngestResponse:
    """Shared ingestion flow for mock and future Gmail mode.

    Beginner note:
    1) adapter fetches raw emails
    2) parser extracts structured fields
    3) AI adds summary/category/priority
    4) storage persists final rows
    """

    adapter = build_ingestion_adapter(mode)
    enrichment_processor = build_enrichment_processor()
    raw_emails = adapter.fetch_emails()
    created: list[ActivityRecord] = []

    for raw in raw_emails:
        parsed = parser.parse(raw)
        enriched = enrichment_processor.enrich(parsed)
        record = storage.create(parsed, enriched)
        created.append(record)

    if created:
        sheets.append_rows(created)

    return IngestResponse(ingested_count=len(created), activities=created)


@router.post("/ingest", response_model=IngestResponse)
def ingest_emails() -> IngestResponse:
    return _run_ingestion(mode=settings.ingestion_mode)


@router.post("/ingest/mock", response_model=IngestResponse)
def ingest_mock_emails() -> IngestResponse:
    return _run_ingestion(mode="mock")
