import json
from pathlib import Path
from uuid import uuid4

from app.models.schemas import ActivityRecord, EnrichedActivity, ParsedEmailActivity


class JSONStorageService:
    """Tiny JSON file storage for local development and demos."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def list_all(self) -> list[ActivityRecord]:
        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [ActivityRecord.model_validate(item) for item in data]

    def get_by_id(self, record_id: str) -> ActivityRecord | None:
        return next((item for item in self.list_all() if item.id == record_id), None)

    def list_high_priority(self, threshold: int = 4) -> list[ActivityRecord]:
        return [item for item in self.list_all() if item.priority >= threshold]

    def create(self, parsed: ParsedEmailActivity, enriched: EnrichedActivity) -> ActivityRecord:
        record = ActivityRecord(
            id=str(uuid4()),
            faculty_name=parsed.faculty_name,
            source_type=parsed.source_type,
            source_url=parsed.source_url,
            raw_text=parsed.raw_text,
            ai_summary=enriched.ai_summary,
            category=enriched.category,
            priority=enriched.priority,
            detected_at=parsed.detected_at,
            review_status=enriched.review_status,
        )

        records = self.list_all()
        records.append(record)
        self.file_path.write_text(
            json.dumps([item.model_dump(mode="json") for item in records], indent=2),
            encoding="utf-8",
        )
        return record
