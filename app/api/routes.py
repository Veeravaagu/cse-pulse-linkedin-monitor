from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import ActivityRecord, IngestResponse
from app.services.ai_processor import AIProcessor
from app.services.gmail_parser import GmailParser
from app.services.ingestion import build_ingestion_adapter
from app.services.sheets_client import GoogleSheetsClient
from app.services.storage import JSONStorageService

router = APIRouter()

parser = GmailParser()
ai_processor = AIProcessor()
storage = JSONStorageService(settings.data_file)
sheets = GoogleSheetsClient(settings.google_sheets_id, settings.google_sheets_worksheet)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/activities", response_model=list[ActivityRecord])
def list_activities() -> list[ActivityRecord]:
    return storage.list_all()


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
    raw_emails = adapter.fetch_emails()
    created: list[ActivityRecord] = []

    for raw in raw_emails:
        parsed = parser.parse(raw)
        enriched = ai_processor.enrich(parsed)
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
