import re
from datetime import datetime

from app.models.schemas import ParsedEmailActivity, RawEmail

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
NAME_PATTERN = re.compile(r"(?:Dr|Prof|Professor)\.?\s+([A-Z][a-z]+\s[A-Z][a-z]+)|([A-Z][a-z]+\s[A-Z][a-z]+)")
NON_PERSON_TITLES = {"Research Matters"}


class GmailParser:
    """Parses LinkedIn-related Gmail notifications into structured activity fields."""

    def parse(self, email: RawEmail) -> ParsedEmailActivity:
        text_blob = f"{email.subject}\n{email.snippet}\n{email.body}".strip()
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
    def _extract_url(text: str) -> str | None:
        match = URL_PATTERN.search(text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_faculty_name(text: str) -> str | None:
        """Simple heuristic for beginner-friendly parsing; replace with NER later."""
        match = NAME_PATTERN.search(text)
        if not match:
            return None
        candidate = match.group(1) or match.group(2)
        if candidate in NON_PERSON_TITLES:
            return None
        return candidate

    @staticmethod
    def _safe_timestamp(value: datetime) -> datetime:
        return value
