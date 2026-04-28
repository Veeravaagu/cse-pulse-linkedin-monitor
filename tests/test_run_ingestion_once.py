from datetime import datetime, timezone

from app.models.schemas import ActivityCategory, ActivityRecord, IngestResponse, ReviewStatus
from scripts.run_ingestion_once import run_once


def test_run_once_uses_injected_ingestion_callable() -> None:
    expected = IngestResponse(
        ingested_count=1,
        activities=[
            ActivityRecord(
                id="activity-1",
                faculty_name=None,
                source_type="ub_cse_email",
                source_url=None,
                raw_text="UB CSE newsletter update.",
                ai_summary="UB CSE newsletter update.",
                category=ActivityCategory.other,
                priority=2,
                detected_at=datetime.now(timezone.utc),
                review_status=ReviewStatus.pending,
            )
        ],
    )

    result = run_once(lambda: expected)

    assert result == expected
