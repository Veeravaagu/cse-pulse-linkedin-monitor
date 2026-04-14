from datetime import datetime, timezone

import pytest

from app.models.schemas import ActivityCategory, RawEmail, ReviewStatus
from app.services.enrichment import LLMProcessor, MockProcessor, build_enrichment_processor
from app.services.gmail_parser import GmailParser


def test_parser_extracts_url_and_name() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="Dr Alice Johnson published a paper",
        sender="notifications-noreply@linkedin.com",
        snippet="New publication in systems.",
        body="Check: https://www.linkedin.com/feed/update/urn:li:activity:999",
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    assert parsed.source_url is not None
    assert "linkedin.com" in parsed.source_url
    assert parsed.faculty_name == "Alice Johnson"


def test_mock_processor_classifies_publication_and_preserves_schema() -> None:
    processor = MockProcessor()
    parser = GmailParser()

    raw = RawEmail(
        subject="Prof Nina Patel publication accepted",
        sender="notifications-noreply@linkedin.com",
        snippet="Journal publication accepted.",
        body="",
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)
    enriched = processor.enrich(parsed)

    assert enriched.category == ActivityCategory.publication
    assert 1 <= enriched.priority <= 5
    assert enriched.review_status == ReviewStatus.pending
    assert enriched.ai_summary


def test_mock_processor_falls_back_to_other() -> None:
    processor = MockProcessor()
    parser = GmailParser()

    raw = RawEmail(
        subject="Faculty update",
        sender="notifications-noreply@linkedin.com",
        snippet="General department note with no known keywords.",
        body="",
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)
    enriched = processor.enrich(parsed)

    assert enriched.category == ActivityCategory.other
    assert enriched.priority == 2


def test_factory_builds_mock_processor() -> None:
    processor = build_enrichment_processor("mock")
    assert isinstance(processor, MockProcessor)


def test_factory_builds_llm_processor() -> None:
    processor = build_enrichment_processor("llm")
    assert isinstance(processor, LLMProcessor)


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported ai_provider"):
        build_enrichment_processor("unknown")
