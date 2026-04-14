import json
from datetime import datetime, timedelta, timezone

from app.models.schemas import ActivityCategory, ReviewStatus
from app.services.digest_service import DigestService
from app.services.storage import JSONStorageService


def _seed_digest_file(file_path: str) -> None:
    now = datetime.now(timezone.utc)
    payload = [
        {
            "id": "activity-1",
            "faculty_name": "Alice Johnson",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/1",
            "raw_text": "Publication accepted in systems journal.",
            "ai_summary": "Publication accepted in a systems journal.",
            "category": ActivityCategory.publication.value,
            "priority": 4,
            "detected_at": (now - timedelta(days=2)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "activity-2",
            "faculty_name": "Bob Lee",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/2",
            "raw_text": "Award received for research.",
            "ai_summary": "Received a research award.",
            "category": ActivityCategory.award.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=1)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "activity-3",
            "faculty_name": "Carla Smith",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/3",
            "raw_text": "Workshop event announced.",
            "ai_summary": "Announced an upcoming workshop.",
            "category": ActivityCategory.event.value,
            "priority": 3,
            "detected_at": (now - timedelta(days=10)).isoformat(),
            "review_status": ReviewStatus.reviewed.value,
        },
    ]
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def test_digest_service_formats_grouped_digest_output(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_digest_file(str(data_file))
    service = DigestService(JSONStorageService(str(data_file)))

    digest = service.generate_preview()

    assert "# Weekly Activity Digest" in digest
    assert "## Award" in digest
    assert "## Publication" in digest
    assert "Received a research award." in digest
    assert "Publication accepted in a systems journal." in digest
    assert "## Event" not in digest


def test_digest_service_filters_by_review_status(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_digest_file(str(data_file))
    service = DigestService(JSONStorageService(str(data_file)))

    digest = service.generate_preview(review_status=ReviewStatus.reviewed)

    assert "Total items: 0" in digest
    assert "No activities matched this digest window." in digest


def test_digest_service_sorts_items_within_group_by_priority(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    now = datetime.now(timezone.utc)
    payload = [
        {
            "id": "activity-1",
            "faculty_name": "Alice Johnson",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/1",
            "raw_text": "First publication.",
            "ai_summary": "Lower priority publication.",
            "category": ActivityCategory.publication.value,
            "priority": 3,
            "detected_at": (now - timedelta(days=1)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "activity-2",
            "faculty_name": "Bob Lee",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/2",
            "raw_text": "Second publication.",
            "ai_summary": "Higher priority publication.",
            "category": ActivityCategory.publication.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=2)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
    ]
    with open(data_file, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    service = DigestService(JSONStorageService(str(data_file)))
    digest = service.generate_preview()

    assert digest.index("Higher priority publication.") < digest.index("Lower priority publication.")


def test_digest_service_returns_structured_grouped_output(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_digest_file(str(data_file))
    service = DigestService(JSONStorageService(str(data_file)))

    digest = service.generate_structured()

    assert digest["review_status"] == "all"
    assert digest["total_items"] == 2
    assert len(digest["sections"]) == 2
    assert digest["sections"][0]["category"] == ActivityCategory.publication.value or digest["sections"][0]["category"] == ActivityCategory.award.value
    assert all("items" in section for section in digest["sections"])


def test_digest_service_returns_empty_structured_state(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    data_file.write_text("[]", encoding="utf-8")
    service = DigestService(JSONStorageService(str(data_file)))

    digest = service.generate_structured(review_status=ReviewStatus.pending)

    assert digest["total_items"] == 0
    assert digest["review_status"] == ReviewStatus.pending.value
    assert digest["sections"] == []


def test_digest_service_applies_max_items_per_category_deterministically(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    now = datetime.now(timezone.utc)
    payload = [
        {
            "id": "activity-1",
            "faculty_name": "Alice Johnson",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/1",
            "raw_text": "Publication A.",
            "ai_summary": "Publication A.",
            "category": ActivityCategory.publication.value,
            "priority": 4,
            "detected_at": (now - timedelta(days=1)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "activity-2",
            "faculty_name": "Bob Lee",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/2",
            "raw_text": "Publication B.",
            "ai_summary": "Publication B.",
            "category": ActivityCategory.publication.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=2)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "activity-3",
            "faculty_name": "Carla Smith",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/3",
            "raw_text": "Publication C.",
            "ai_summary": "Publication C.",
            "category": ActivityCategory.publication.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=1, hours=1)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
    ]
    with open(data_file, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    service = DigestService(JSONStorageService(str(data_file)))
    digest = service.generate_structured(max_items_per_category=2)

    items = digest["sections"][0]["items"]
    assert len(items) == 2
    assert [item["id"] for item in items] == ["activity-3", "activity-2"]


def test_markdown_export_formats_sections_in_deterministic_category_order(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    _seed_digest_file(str(data_file))
    service = DigestService(JSONStorageService(str(data_file)))

    markdown = service.generate_markdown_export(include_section_totals=True)

    assert markdown.index("## Publication (1)") < markdown.index("## Award (1)")


def test_markdown_export_applies_max_item_trimming_and_summary_truncation(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    now = datetime.now(timezone.utc)
    payload = [
        {
            "id": "activity-1",
            "faculty_name": "Alice Johnson",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/1",
            "raw_text": "Publication A.",
            "ai_summary": "A very long summary about publication alpha.",
            "category": ActivityCategory.publication.value,
            "priority": 4,
            "detected_at": (now - timedelta(days=1)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
        {
            "id": "activity-2",
            "faculty_name": "Bob Lee",
            "source_type": "linkedin_email",
            "source_url": "https://www.linkedin.com/feed/update/2",
            "raw_text": "Publication B.",
            "ai_summary": "A very long summary about publication beta.",
            "category": ActivityCategory.publication.value,
            "priority": 5,
            "detected_at": (now - timedelta(days=2)).isoformat(),
            "review_status": ReviewStatus.pending.value,
        },
    ]
    with open(data_file, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    service = DigestService(JSONStorageService(str(data_file)))
    markdown = service.generate_markdown_export(max_items_per_category=1, summary_max_length=20)

    assert markdown.count("- [P") == 1
    assert "A very long summa..." in markdown


def test_preview_and_markdown_export_stay_consistent_on_empty_state(tmp_path) -> None:
    data_file = tmp_path / "activities.json"
    data_file.write_text("[]", encoding="utf-8")
    service = DigestService(JSONStorageService(str(data_file)))

    preview = service.generate_preview(review_status=ReviewStatus.pending)
    markdown = service.generate_markdown_export(review_status=ReviewStatus.pending)

    assert "No activities matched this digest window." in preview
    assert "No activities matched this digest window." in markdown
