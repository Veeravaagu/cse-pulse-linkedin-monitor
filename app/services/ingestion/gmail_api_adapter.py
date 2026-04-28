import base64
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.models.schemas import RawEmail

logger = logging.getLogger(__name__)
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
LINKEDIN_NEWS_MARKERS = (
    "editors-noreply@linkedin.com",
    "linkedin news",
    "suggested top conversations",
    "see the story",
    "gain more insights on this developing story",
)
LINKEDIN_INVITATION_MARKERS = (
    "i want to connect",
    "is waiting for your response",
    "invitation",
    "accept:",
    "view profile:",
    "build your network",
    "linkedin invitations",
)
UB_CSE_INSTITUTION_MARKERS = (
    "university at buffalo",
    "ub cse",
    "department of computer science and engineering",
    "computer science and engineering",
    "school of engineering and applied sciences",
    "engineering.buffalo.edu",
    "cse.buffalo.edu",
    "doermann@buffalo.edu",
    "buffalo.edu",
)
UB_CSE_ACTIVITY_MARKERS = (
    "award",
    "grant",
    "publication",
    "published",
    "research",
    "seminar",
    "talk",
    "event",
    "conference",
    "student",
    "faculty",
    "professor",
    "phd",
    "startup",
    "funding",
)


def is_likely_linkedin_email(raw_email: RawEmail) -> bool:
    sender = raw_email.sender.lower()
    subject = raw_email.subject.lower()
    body = raw_email.body.lower()

    return (
        "linkedin.com" in sender
        or "linkedin" in subject
        or "linkedin.com" in body
        or "www.linkedin.com" in body
        or "linkedin notification" in body
    )


def is_likely_faculty_activity_email(raw_email: RawEmail) -> bool:
    text = " ".join([raw_email.sender, raw_email.subject, raw_email.body]).lower()
    return not any(marker in text for marker in LINKEDIN_NEWS_MARKERS)


def is_relevant_activity_email(raw_email: RawEmail) -> bool:
    text = " ".join([raw_email.subject, raw_email.body]).lower()
    return not any(marker in text for marker in LINKEDIN_INVITATION_MARKERS)


def is_likely_ub_cse_activity_email(raw_email: RawEmail) -> bool:
    text = " ".join([raw_email.sender, raw_email.subject, raw_email.body]).lower()
    return any(marker in text for marker in UB_CSE_INSTITUTION_MARKERS)


class GmailAPIIngestionAdapter:
    """Read-only Gmail API ingestion adapter.

    If credentials are missing or unusable, it returns an empty batch safely.
    """

    def __init__(
        self,
        query: str,
        max_results: int,
        credentials_path: str = "",
        oauth_client_secret_path: str | None = None,
        token_path: str | None = None,
        received_after: datetime | None = None,
        service_builder: Callable[[], Any | None] | None = None,
    ) -> None:
        self.query = query
        self.max_results = max_results
        self.credentials_path = credentials_path
        self.received_after = received_after
        if oauth_client_secret_path is None or token_path is None:
            from app.config import settings

            if oauth_client_secret_path is None:
                oauth_client_secret_path = settings.gmail_oauth_client_secret_path
            if token_path is None:
                token_path = settings.gmail_token_path
        self.oauth_client_secret_path = oauth_client_secret_path
        self.token_path = token_path
        self.service_builder = service_builder or self._build_gmail_service
        self.last_fetch_succeeded = False

    def fetch_emails(self) -> list[RawEmail]:
        self.last_fetch_succeeded = False
        try:
            service = self.service_builder()
            if service is None:
                return []

            message_refs = (
                service.users()
                .messages()
                .list(userId="me", q=self._query(), maxResults=self.max_results)
                .execute()
                .get("messages")
                or []
            )
            messages = []
            for message_ref in message_refs:
                message_id = message_ref.get("id")
                if not message_id:
                    continue
                messages.append(
                    service.users()
                    .messages()
                    .get(userId="me", id=message_id, format="full")
                    .execute()
                )

            self.last_fetch_succeeded = True
            return self.convert_messages(messages)
        except Exception:
            logger.exception("Gmail read-only ingestion failed; returning empty batch.")
            return []

    def _build_gmail_service(self) -> Any | None:
        credentials = self._load_credentials()
        if credentials is None:
            return None

        return self._build_service(credentials)

    def _load_credentials(self) -> Any | None:
        if self.credentials_path.strip():
            return self._load_service_account_credentials()

        return self._load_oauth_credentials()

    def _load_service_account_credentials(self) -> Any | None:
        credentials_file = Path(self.credentials_path)
        if not credentials_file.exists():
            logger.info("Gmail credentials path does not exist; returning empty batch.")
            return None

        try:
            from google.oauth2.service_account import Credentials
        except ImportError:
            logger.exception("Gmail service-account dependencies are unavailable.")
            return None

        return Credentials.from_service_account_file(
            str(credentials_file),
            scopes=[GMAIL_READONLY_SCOPE],
        )

    def _load_oauth_credentials(self) -> Any | None:
        if not self.oauth_client_secret_path.strip() and not self.token_path.strip():
            logger.info("Gmail credentials are not configured; returning empty batch.")
            return None

        if not self.token_path.strip():
            logger.info("Gmail OAuth token path is not configured; returning empty batch.")
            return None

        token_file = Path(self.token_path)
        if not token_file.exists():
            logger.info("Gmail OAuth token does not exist; returning empty batch.")
            return None

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
        except ImportError:
            logger.exception("Gmail OAuth dependencies are unavailable.")
            return None

        credentials = Credentials.from_authorized_user_file(
            str(token_file),
            scopes=[GMAIL_READONLY_SCOPE],
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            token_file.write_text(credentials.to_json(), encoding="utf-8")

        if not credentials.valid:
            logger.info("Gmail OAuth token is invalid; returning empty batch.")
            return None

        return credentials

    def _build_service(self, credentials: Any) -> Any:
        from googleapiclient.discovery import build

        return build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def _query(self) -> str:
        if self.received_after is None:
            return self.query

        after = self.received_after.astimezone(timezone.utc).strftime("%Y/%m/%d")
        if f"after:{after}" in self.query:
            return self.query
        return f"{self.query} after:{after}".strip()

    def convert_messages(self, messages: list[dict[str, Any]]) -> list[RawEmail]:
        raw_emails = [self._convert_message(message) for message in messages]
        return [
            raw_email
            for raw_email in raw_emails
            if (
                is_likely_faculty_activity_email(raw_email)
                and is_relevant_activity_email(raw_email)
                and (is_likely_linkedin_email(raw_email) or is_likely_ub_cse_activity_email(raw_email))
            )
        ]

    def _convert_message(self, message: dict[str, Any]) -> RawEmail:
        payload = message.get("payload") or {}
        headers = self._headers_by_name(payload)
        snippet = str(message.get("snippet") or "")

        return RawEmail(
            subject=headers.get("subject", ""),
            sender=headers.get("from", ""),
            snippet=snippet,
            body=self._extract_body(payload) or snippet,
            received_at=self._received_at(message),
        )

    @staticmethod
    def _headers_by_name(payload: dict[str, Any]) -> dict[str, str]:
        headers: dict[str, str] = {}
        for header in payload.get("headers") or []:
            name = str(header.get("name") or "").lower()
            if name:
                headers[name] = str(header.get("value") or "")
        return headers

    @classmethod
    def _extract_body(cls, payload: dict[str, Any]) -> str:
        plain = cls._find_body_part(payload, "text/plain")
        if plain:
            return plain

        html = cls._find_body_part(payload, "text/html")
        if html:
            return html

        return ""

    @classmethod
    def _find_body_part(cls, payload: dict[str, Any], mime_type: str) -> str:
        if payload.get("mimeType") == mime_type:
            decoded = cls._decode_body_data(payload.get("body") or {})
            if decoded:
                return decoded

        for part in payload.get("parts") or []:
            decoded = cls._find_body_part(part, mime_type)
            if decoded:
                return decoded

        return ""

    @staticmethod
    def _decode_body_data(body: dict[str, Any]) -> str:
        data = body.get("data")
        if not data:
            return ""

        padded = str(data) + "=" * (-len(str(data)) % 4)
        try:
            return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        except Exception:
            return ""

    @staticmethod
    def _received_at(message: dict[str, Any]) -> datetime:
        try:
            timestamp_ms = int(str(message.get("internalDate") or "0"))
        except ValueError:
            timestamp_ms = 0
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
