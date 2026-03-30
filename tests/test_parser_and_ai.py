from datetime import datetime, timezone

from app.models.schemas import ActivityCategory, RawEmail
from app.services.ai_processor import AIProcessor
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


def test_ai_classifier_publication() -> None:
    processor = AIProcessor()
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
