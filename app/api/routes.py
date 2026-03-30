import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import ActivityRecord, IngestResponse, RawEmail
from app.services.ai_processor import AIProcessor
from app.services.gmail_parser import GmailParser
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


@router.post("/ingest/mock", response_model=IngestResponse)
def ingest_mock_emails() -> IngestResponse:
    mock_file = Path("data/mock_emails/linkedin_notifications.json")
    if not mock_file.exists():
        raise HTTPException(status_code=500, detail="Mock data file missing")

    payload = json.loads(mock_file.read_text(encoding="utf-8"))
    created: list[ActivityRecord] = []

    for item in payload:
        raw = RawEmail.model_validate(item)
        parsed = parser.parse(raw)
        enriched = ai_processor.enrich(parsed)
        record = storage.create(parsed, enriched)
        created.append(record)

    sheets.append_rows(created)
    return IngestResponse(ingested_count=len(created), activities=created)
