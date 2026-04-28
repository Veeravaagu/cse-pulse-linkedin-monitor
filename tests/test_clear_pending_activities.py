import json
from datetime import datetime, timezone

from scripts.clear_pending_activities import clear_pending_activities


def _activity(record_id: str, review_status: str) -> dict[str, object]:
    return {
        "id": record_id,
        "faculty_name": "Example Faculty",
        "source_type": "linkedin_email",
        "source_url": f"https://www.linkedin.com/feed/update/{record_id}",
        "raw_text": f"{record_id} raw text",
        "ai_summary": f"{record_id} summary",
        "category": "publication",
        "priority": 3,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "review_status": review_status,
    }


def test_clear_pending_activities_preserves_approved_and_rejected(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    data_file.write_text(
        json.dumps(
            [
                _activity("pending-1", "pending"),
                _activity("approved-1", "approved"),
                _activity("rejected-1", "rejected"),
            ]
        ),
        encoding="utf-8",
    )

    result = clear_pending_activities(data_file)

    remaining = json.loads(data_file.read_text(encoding="utf-8"))
    assert result == {"removed": 1, "preserved": 2}
    assert [item["id"] for item in remaining] == ["approved-1", "rejected-1"]
    assert [item["review_status"] for item in remaining] == ["approved", "rejected"]


def test_clear_pending_activities_removes_only_pending(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    data_file.write_text(
        json.dumps(
            [
                _activity("pending-1", "pending"),
                _activity("pending-2", "pending"),
                _activity("approved-1", "approved"),
                _activity("rejected-1", "rejected"),
                _activity("reviewed-1", "reviewed"),
            ]
        ),
        encoding="utf-8",
    )

    result = clear_pending_activities(data_file)

    remaining = json.loads(data_file.read_text(encoding="utf-8"))
    assert result == {"removed": 2, "preserved": 3}
    assert [item["id"] for item in remaining] == ["approved-1", "rejected-1", "reviewed-1"]
