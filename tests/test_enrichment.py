from datetime import datetime, timezone

import pytest

from app.models.schemas import ActivityCategory, ParsedEmailActivity, RawEmail, ReviewStatus
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


def test_parser_does_not_treat_research_matters_as_faculty_name() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="Research Matters: UB CSE faculty receive new funding",
        sender="news@buffalo.edu",
        snippet="University at Buffalo research update",
        body=(
            "University at Buffalo Department of Computer Science and Engineering "
            "faculty received research funding for a new AI project."
        ),
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    assert parsed.faculty_name is None


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


def test_mock_processor_uses_other_for_research_matters_ub_cse_newsletter() -> None:
    processor = MockProcessor()
    parsed = ParsedEmailActivity(
        faculty_name=None,
        source_type="ub_cse_email",
        source_url="http://cse.buffalo.edu/~doermann",
        raw_text=(
            "FW: Research Matters: Updates from Research, Innovation and Economic Development\n"
            "University at Buffalo faculty research funding opportunities and publications newsletter."
        ),
        detected_at=datetime.now(timezone.utc),
    )

    enriched = processor.enrich(parsed)

    assert enriched.category == ActivityCategory.other
    assert enriched.priority == 2


def test_mock_processor_classifies_obvious_grant_text() -> None:
    processor = MockProcessor()
    parsed = ParsedEmailActivity(
        raw_text="The lab received a new NSF grant for computing systems research.",
        detected_at=datetime.now(timezone.utc),
    )

    enriched = processor.enrich(parsed)

    assert enriched.category == ActivityCategory.grant


def test_mock_processor_classifies_obvious_award_text() -> None:
    processor = MockProcessor()
    parsed = ParsedEmailActivity(
        raw_text="A CSE team won a major research award.",
        detected_at=datetime.now(timezone.utc),
    )

    enriched = processor.enrich(parsed)

    assert enriched.category == ActivityCategory.award


def test_mock_processor_classifies_obvious_talk_event_text() -> None:
    processor = MockProcessor()
    parsed = ParsedEmailActivity(
        raw_text="Upcoming CSE seminar and workshop event announced.",
        detected_at=datetime.now(timezone.utc),
    )

    enriched = processor.enrich(parsed)

    assert enriched.category == ActivityCategory.talk_event


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
