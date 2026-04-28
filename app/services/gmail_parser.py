import re
from datetime import datetime

from app.models.schemas import ParsedEmailActivity, RawEmail

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
NAME_PATTERN = re.compile(r"(?:Dr|Prof|Professor)\.?\s+([A-Z][a-z]+\s[A-Z][a-z]+)|([A-Z][a-z]+\s[A-Z][a-z]+)")
FORWARD_PREFIX_PATTERN = re.compile(r"^(?:(?:fw|fwd|re):\s*)+", re.IGNORECASE)
PREFERRED_URL_MARKERS = (
    "engineering.buffalo.edu",
    "latest_news",
    "news-events",
    "detail.html",
    "/news.html",
)
DEPRIORITIZED_URL_MARKERS = (
    "cse.buffalo.edu/~doermann",
    "forms.office.com",
    "bookwithme",
    "outlook.office.com",
    "unsubscribe",
    "mailchi.mp",
    "mailchimp.com",
    "view-in-browser",
)
NON_PERSON_TITLES = {
    "Annual Research",
    "Buffalo Department",
    "Computer Science",
    "Research Matters",
    "Research Report",
    "Science Engineering",
    "University Buffalo",
}


class GmailParser:
    """Parses LinkedIn-related Gmail notifications into structured activity fields."""

    def parse(self, email: RawEmail) -> ParsedEmailActivity:
        subject = self._clean_subject(email.subject)
        text_blob = "\n".join(part for part in (subject, email.snippet, email.body) if part).strip()
        source_url = self._extract_url(text_blob)
        faculty_name = self._extract_faculty_name(text_blob)

        return ParsedEmailActivity(
            faculty_name=faculty_name,
            source_type="linkedin_email",
            source_url=source_url,
            raw_text=text_blob,
            detected_at=self._safe_timestamp(email.received_at),
        )

    @staticmethod
    def _clean_subject(subject: str) -> str:
        return FORWARD_PREFIX_PATTERN.sub("", subject).strip()

    @staticmethod
    def _extract_url(text: str) -> str | None:
        urls = URL_PATTERN.findall(text)
        if not urls:
            return None
        return max(enumerate(urls), key=lambda item: (GmailParser._score_url(item[1]), -item[0]))[1]

    @staticmethod
    def _score_url(url: str) -> int:
        lowered = url.lower().rstrip(".,);]")
        score = 0
        if "buffalo.edu" in lowered:
            score += 2
        if "cse.buffalo.edu" in lowered and "/~doermann" not in lowered:
            score += 2
        if any(marker in lowered for marker in PREFERRED_URL_MARKERS):
            score += 4
        if any(marker in lowered for marker in DEPRIORITIZED_URL_MARKERS):
            score -= 6
        return score

    @staticmethod
    def _extract_faculty_name(text: str) -> str | None:
        """Simple heuristic for beginner-friendly parsing; replace with NER later."""
        for match in NAME_PATTERN.finditer(text):
            candidate = match.group(1) or match.group(2)
            if candidate not in NON_PERSON_TITLES:
                return candidate
        return None

    @staticmethod
    def _safe_timestamp(value: datetime) -> datetime:
        return value
