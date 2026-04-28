import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from app.models.schemas import ActivityCategory, ActivityRecord, EnrichedActivity, ParsedEmailActivity, ReviewStatus
from app.services.storage_base import ActivityStorage


class JSONStorageService(ActivityStorage):
    """Tiny JSON file storage for local development and demos."""

    LEGACY_CATEGORY_MAP = {
        "talk": ActivityCategory.talk_event.value,
        "event": ActivityCategory.talk_event.value,
        "student achievement": ActivityCategory.faculty_student.value,
    }

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def list_all(self) -> list[ActivityRecord]:
        return self._read_records()

    def list_activities(
        self,
        *,
        category: ActivityCategory | None = None,
        review_status: ReviewStatus | None = None,
        sort_by: str = "detected_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int | None = None,
        days: int | None = None,
    ) -> list[ActivityRecord]:
        """Return dashboard-friendly activity rows with optional filtering.

        Beginner note:
        - filtering happens before sorting
        - sorting happens before pagination
        - pagination is simple offset/limit so the response shape stays unchanged
        """

        records = self._read_records()

        if category is not None:
            records = [item for item in records if item.category == category]
        if review_status is not None:
            records = [item for item in records if item.review_status == review_status]
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            records = [item for item in records if self._as_aware_datetime(item.detected_at) >= cutoff]

        records = self._sort_records(records, sort_by=sort_by, sort_order=sort_order)

        if offset:
            records = records[offset:]
        if limit is not None:
            records = records[:limit]

        return records

    def get_by_id(self, record_id: str) -> ActivityRecord | None:
        return next((item for item in self.list_all() if item.id == record_id), None)

    def update_review_status(self, record_id: str, review_status: ReviewStatus) -> ActivityRecord | None:
        records = self._read_records()
        for index, record in enumerate(records):
            if record.id == record_id:
                updated = record.model_copy(update={"review_status": review_status})
                records[index] = updated
                self._write_records(records)
                return updated
        return None

    def delete_rejected(self, record_id: str) -> bool:
        return self.delete_rejected_many([record_id]) == 1

    def delete_rejected_many(self, record_ids: list[str]) -> int:
        ids = set(record_ids)
        records = self._read_records()
        kept_records = [
            record
            for record in records
            if not (record.id in ids and record.review_status == ReviewStatus.rejected)
        ]
        deleted_count = len(records) - len(kept_records)

        if deleted_count:
            self._write_records(kept_records)

        return deleted_count

    def list_high_priority(self, threshold: int = 4) -> list[ActivityRecord]:
        records = [item for item in self._read_records() if item.priority >= threshold]
        return self._sort_records(records, sort_by="priority", sort_order="desc")

    def exists_by_source_url(self, source_url: str) -> bool:
        return any(item.source_url == source_url for item in self._read_records())

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

        records = self._read_records()
        records.append(record)
        self._write_records(records)
        return record

    def _read_records(self) -> list[ActivityRecord]:
        raw_text = self.file_path.read_text(encoding="utf-8").strip()
        if not raw_text:
            return []

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            # Beginner note:
            # a local JSON file can become corrupted during manual edits or
            # interrupted runs. Returning an empty list keeps dashboard reads safe
            # and lets the next successful write restore the file.
            return []

        return [ActivityRecord.model_validate(self._normalize_record(item)) for item in data]

    def _write_records(self, records: list[ActivityRecord]) -> None:
        """Write atomically so partial writes do not leave broken JSON behind."""

        with NamedTemporaryFile("w", encoding="utf-8", dir=self.file_path.parent, delete=False) as handle:
            json.dump([item.model_dump(mode="json") for item in records], handle, indent=2)
            handle.flush()
            self._replace_file(Path(handle.name))

    def _replace_file(self, temp_path: Path) -> None:
        """Swap the temp file into place as the final storage file."""

        temp_path.replace(self.file_path)

    @classmethod
    def _normalize_record(cls, item: dict[str, object]) -> dict[str, object]:
        category = item.get("category")
        if isinstance(category, str) and category in cls.LEGACY_CATEGORY_MAP:
            return {**item, "category": cls.LEGACY_CATEGORY_MAP[category]}
        return item

    @staticmethod
    def _sort_records(records: list[ActivityRecord], *, sort_by: str, sort_order: str) -> list[ActivityRecord]:
        reverse = sort_order == "desc"

        if sort_by == "priority":
            return sorted(records, key=lambda item: (item.priority, item.detected_at), reverse=reverse)

        return sorted(records, key=lambda item: (item.detected_at, item.priority), reverse=reverse)

    @staticmethod
    def _as_aware_datetime(value: object) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is not None:
            return value
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc)
        raise TypeError("detected_at must be a datetime")
