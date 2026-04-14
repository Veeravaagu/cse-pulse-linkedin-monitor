import json
from datetime import datetime, timezone
from pathlib import Path

from app.models.schemas import ActivityCategory, EnrichedActivity, ParsedEmailActivity, ReviewStatus
from app.services.storage import JSONStorageService


def _sample_parsed_activity() -> ParsedEmailActivity:
    return ParsedEmailActivity(
        faculty_name="Alice Johnson",
        source_type="linkedin_email",
        source_url="https://www.linkedin.com/feed/update/1",
        raw_text="Publication accepted in systems journal.",
        detected_at=datetime.now(timezone.utc),
    )


def _sample_enriched_activity() -> EnrichedActivity:
    return EnrichedActivity(
        ai_summary="Publication accepted.",
        category=ActivityCategory.publication,
        priority=5,
        review_status=ReviewStatus.pending,
    )


def test_json_storage_supports_normal_reads_and_writes(tmp_path) -> None:
    storage = JSONStorageService(str(tmp_path / "activities.json"))

    created = storage.create(_sample_parsed_activity(), _sample_enriched_activity())
    records = storage.list_all()

    assert len(records) == 1
    assert records[0].id == created.id
    assert records[0].category == ActivityCategory.publication
    assert storage.get_by_id(created.id) is not None


def test_json_storage_uses_atomic_replace_on_write(tmp_path, monkeypatch) -> None:
    storage = JSONStorageService(str(tmp_path / "activities.json"))
    replaced: dict[str, Path] = {}
    original_replace = storage._replace_file

    def tracking_replace(temp_path: Path) -> None:
        replaced["temp_path"] = temp_path
        original_replace(temp_path)

    monkeypatch.setattr(storage, "_replace_file", tracking_replace)

    storage.create(_sample_parsed_activity(), _sample_enriched_activity())

    assert "temp_path" in replaced
    assert replaced["temp_path"] != storage.file_path
    assert storage.file_path.exists()
    saved = json.loads(storage.file_path.read_text(encoding="utf-8"))
    assert len(saved) == 1


def test_json_storage_treats_empty_file_as_no_records(tmp_path) -> None:
    file_path = tmp_path / "activities.json"
    file_path.write_text("", encoding="utf-8")
    storage = JSONStorageService(str(file_path))

    assert storage.list_all() == []
    assert storage.list_activities() == []


def test_json_storage_treats_corrupted_file_as_no_records(tmp_path) -> None:
    file_path = tmp_path / "activities.json"
    file_path.write_text("{not valid json", encoding="utf-8")
    storage = JSONStorageService(str(file_path))

    assert storage.list_all() == []
    assert storage.get_by_id("missing") is None
