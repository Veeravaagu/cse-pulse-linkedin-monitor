import json
from datetime import datetime, timezone

from scripts.clear_pending_activities import clear_pending_activities
from scripts.reset_local_ingestion_state import reset_local_ingestion_state


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


def _write_state(state_file) -> None:
    state_file.write_text(
        json.dumps({"last_successful_ingestion_at": "2026-04-27T12:00:00+00:00"}),
        encoding="utf-8",
    )


def test_reset_local_ingestion_state_clears_pending_and_resets_cursor(tmp_path) -> None:
    activities_file = tmp_path / "activities.json"
    state_file = tmp_path / "ingestion_state.json"
    activities_file.write_text(
        json.dumps(
            [
                _activity("pending-1", "pending"),
                _activity("approved-1", "approved"),
                _activity("rejected-1", "rejected"),
            ]
        ),
        encoding="utf-8",
    )
    _write_state(state_file)

    result = reset_local_ingestion_state(activities_file=activities_file, state_file=state_file)

    remaining = json.loads(activities_file.read_text(encoding="utf-8"))
    assert result == {"removed_activities": 1, "preserved_activities": 2, "cursor_reset": True}
    assert [item["id"] for item in remaining] == ["approved-1", "rejected-1"]
    assert not state_file.exists()


def test_reset_local_ingestion_state_all_flag_clears_all_activities_and_cursor(tmp_path) -> None:
    activities_file = tmp_path / "activities.json"
    state_file = tmp_path / "ingestion_state.json"
    activities_file.write_text(
        json.dumps(
            [
                _activity("pending-1", "pending"),
                _activity("approved-1", "approved"),
                _activity("rejected-1", "rejected"),
            ]
        ),
        encoding="utf-8",
    )
    _write_state(state_file)

    result = reset_local_ingestion_state(
        activities_file=activities_file,
        state_file=state_file,
        clear_all=True,
    )

    assert result == {"removed_activities": 3, "preserved_activities": 0, "cursor_reset": True}
    assert json.loads(activities_file.read_text(encoding="utf-8")) == []
    assert not state_file.exists()


def test_clear_pending_activities_does_not_reset_cursor(tmp_path) -> None:
    activities_file = tmp_path / "activities.json"
    state_file = tmp_path / "ingestion_state.json"
    activities_file.write_text(json.dumps([_activity("pending-1", "pending")]), encoding="utf-8")
    _write_state(state_file)
    before = state_file.read_text(encoding="utf-8")

    result = clear_pending_activities(activities_file)

    assert result == {"removed": 1, "preserved": 0}
    assert state_file.exists()
    assert state_file.read_text(encoding="utf-8") == before
