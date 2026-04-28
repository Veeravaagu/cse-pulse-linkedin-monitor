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


def test_parser_prefers_ub_engineering_article_over_doermann_signature_url() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="FW: UB Engineering article",
        sender="David Doermann <doermann@buffalo.edu>",
        snippet="Forwarded news item",
        body=(
            "David Doermann\n"
            "website: http://cse.buffalo.edu/~doermann\n"
            "Read the article: https://engineering.buffalo.edu/news/latest_news.host.html/content/shared/engineering/home/articles/2026/cse-research.detail.html"
        ),
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    assert (
        parsed.source_url
        == "https://engineering.buffalo.edu/news/latest_news.host.html/content/shared/engineering/home/articles/2026/cse-research.detail.html"
    )


def test_parser_prefers_cse_news_page_over_doermann_signature_url() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="FW: Faculty news",
        sender="David Doermann <doermann@buffalo.edu>",
        snippet="Forwarded CSE item",
        body=(
            "website: http://cse.buffalo.edu/~doermann\n"
            "Related news: https://cse.buffalo.edu/~wenyaoxu/news.html"
        ),
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    assert parsed.source_url == "https://cse.buffalo.edu/~wenyaoxu/news.html"


def test_parser_still_extracts_single_meaningful_url() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="UB CSE article",
        sender="news@buffalo.edu",
        snippet="Article link",
        body="Read more: https://engineering.buffalo.edu/news-events/news.host.html/content/shared/engineering/home/articles/2026/example.detail.html",
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    assert (
        parsed.source_url
        == "https://engineering.buffalo.edu/news-events/news.host.html/content/shared/engineering/home/articles/2026/example.detail.html"
    )


def test_parser_does_not_choose_footer_url_over_activity_url() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="Research update",
        sender="news@buffalo.edu",
        snippet="View in browser link appears before article",
        body=(
            "View in browser: https://mailchi.mp/example/research-matters\n"
            "Main story: https://engineering.buffalo.edu/news-events/news.host.html/content/shared/engineering/home/articles/2026/grant-award.detail.html\n"
            "Unsubscribe: https://mailchimp.com/unsubscribe/example"
        ),
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    assert (
        parsed.source_url
        == "https://engineering.buffalo.edu/news-events/news.host.html/content/shared/engineering/home/articles/2026/grant-award.detail.html"
    )


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


def test_parser_cleans_forwarded_newsletter_subject_prefix() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="FW: Research Matters: Updates from Research, Innovation and Economic Development",
        sender="news@buffalo.edu",
        snippet="CSE Seminar: Trustworthy AI talk announced for Friday.",
        body="",
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    first_line = parsed.raw_text.splitlines()[0]
    assert first_line == "Research Matters: Updates from Research, Innovation and Economic Development"
    assert not first_line.startswith(("FW:", "Fwd:", "RE:"))


def test_ub_cse_newsletter_item_gets_readable_summary_and_headline() -> None:
    processor = MockProcessor()
    parsed = ParsedEmailActivity(
        faculty_name=None,
        source_type="ub_cse_email",
        source_url="https://engineering.buffalo.edu/computer-science-engineering/news.html",
        raw_text=(
            "Research Matters: Updates from Research, Innovation and Economic Development\n"
            "IN THIS ISSUE: Annual Research Report | Events | News\n"
            "View in browser: https://mailchi.mp/buffalo/research-matters\n"
            "Home | News | Events | Contact\n"
            "CSE Seminar: Trustworthy AI for autonomous systems\n"
            "Professor Maya Lee will present a CSE seminar on trustworthy AI for autonomous systems this Friday.\n"
            "Follow us on LinkedIn, Facebook, and Instagram\n"
            "Unsubscribe: https://mailchimp.com/unsubscribe/example"
        ),
        detected_at=datetime.now(timezone.utc),
    )

    enriched = processor.enrich(parsed)

    assert parsed.faculty_name == "CSE Seminar: Trustworthy AI for autonomous systems"
    assert enriched.category == ActivityCategory.talk_event
    assert enriched.ai_summary == (
        "CSE Seminar: Trustworthy AI for autonomous systems. "
        "Professor Maya Lee will present a CSE seminar on trustworthy AI for autonomous systems this Friday."
    )
    assert "Research Matters" not in enriched.ai_summary
    assert "View in browser" not in enriched.ai_summary
    assert "Home | News | Events | Contact" not in enriched.ai_summary
    assert "Unsubscribe" not in enriched.ai_summary


def test_parser_extracts_obvious_person_from_newsletter_body() -> None:
    parser = GmailParser()
    raw = RawEmail(
        subject="Research Matters: Faculty highlights",
        sender="news@buffalo.edu",
        snippet="Professor Maya Lee received an NSF grant for secure systems research.",
        body="",
        received_at=datetime.now(timezone.utc),
    )

    parsed = parser.parse(raw)

    assert parsed.faculty_name == "Maya Lee"


def test_newsletter_fallback_keeps_safe_generic_behavior() -> None:
    processor = MockProcessor()
    parsed = ParsedEmailActivity(
        faculty_name=None,
        source_type="ub_cse_email",
        source_url=None,
        raw_text=(
            "Research Matters: Updates from Research, Innovation and Economic Development\n"
            "IN THIS ISSUE: Annual Research Report | Resources | Events\n"
            "University at Buffalo research newsletter for the campus community."
        ),
        detected_at=datetime.now(timezone.utc),
    )

    enriched = processor.enrich(parsed)

    assert parsed.faculty_name is None
    assert enriched.category == ActivityCategory.other
    assert enriched.priority == 2
    assert enriched.ai_summary == "University at Buffalo research newsletter for the campus community."


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
