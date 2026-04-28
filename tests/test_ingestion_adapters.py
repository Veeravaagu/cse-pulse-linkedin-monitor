import base64
import json
from datetime import datetime, timezone

import pytest

from app.services.ingestion.factory import build_ingestion_adapter
from app.models.schemas import RawEmail
from app.services.ingestion.gmail_api_adapter import (
    GmailAPIIngestionAdapter,
    is_likely_faculty_activity_email,
    is_likely_linkedin_email,
    is_likely_ub_cse_activity_email,
    is_relevant_activity_email,
)
from app.services.ingestion.mock_adapter import MockGmailIngestionAdapter


def _base64url(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("utf-8").rstrip("=")


def test_mock_adapter_reads_local_payload(tmp_path) -> None:
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(
        json.dumps(
            [
                {
                    "subject": "Prof Maya Lee received an award",
                    "sender": "notifications-noreply@linkedin.com",
                    "snippet": "Award announcement",
                    "body": "https://www.linkedin.com/feed/update/urn:li:activity:123",
                    "received_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        ),
        encoding="utf-8",
    )

    adapter = MockGmailIngestionAdapter(payload_path=str(payload_file))
    records = adapter.fetch_emails()

    assert len(records) == 1
    assert records[0].subject.startswith("Prof Maya Lee")


def test_factory_selects_mock_mode() -> None:
    adapter = build_ingestion_adapter(mode="mock")
    assert isinstance(adapter, MockGmailIngestionAdapter)


def test_factory_selects_gmail_mode() -> None:
    adapter = build_ingestion_adapter(mode="gmail")
    assert isinstance(adapter, GmailAPIIngestionAdapter)


def test_factory_rejects_unknown_mode_instead_of_falling_back_to_mock() -> None:
    with pytest.raises(ValueError, match="Unsupported ingestion_mode"):
        build_ingestion_adapter(mode="demo")


def test_gmail_adapter_scaffold_is_safe_placeholder() -> None:
    adapter = GmailAPIIngestionAdapter(query="from:linkedin.com", max_results=10)
    assert adapter.fetch_emails() == []


def test_gmail_adapter_prefers_service_account_credentials(tmp_path, monkeypatch) -> None:
    credentials_file = tmp_path / "service-account.json"
    credentials_file.write_text("{}", encoding="utf-8")
    token_file = tmp_path / "token.json"
    token_file.write_text("{}", encoding="utf-8")
    loaded: dict[str, object] = {}

    class FakeServiceAccountCredentials:
        pass

    fake_credentials = FakeServiceAccountCredentials()

    from google.oauth2.service_account import Credentials

    def fake_from_service_account_file(cls, path: str, scopes: list[str]) -> FakeServiceAccountCredentials:
        loaded["path"] = path
        loaded["scopes"] = scopes
        return fake_credentials

    monkeypatch.setattr(
        Credentials,
        "from_service_account_file",
        classmethod(fake_from_service_account_file),
    )

    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        credentials_path=str(credentials_file),
        oauth_client_secret_path=str(tmp_path / "client-secret.json"),
        token_path=str(token_file),
    )
    monkeypatch.setattr(adapter, "_build_service", lambda credentials: credentials)

    credentials = adapter._build_gmail_service()

    assert credentials is fake_credentials
    assert loaded == {
        "path": str(credentials_file),
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    }


def test_gmail_adapter_loads_existing_oauth_token(tmp_path, monkeypatch) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("{}", encoding="utf-8")
    loaded: dict[str, object] = {}

    class FakeCredentials:
        expired = False
        refresh_token = "refresh-token"
        valid = True

    from google.oauth2.credentials import Credentials

    def fake_from_authorized_user_file(cls, path: str, scopes: list[str]) -> FakeCredentials:
        loaded["path"] = path
        loaded["scopes"] = scopes
        return FakeCredentials()

    monkeypatch.setattr(
        Credentials,
        "from_authorized_user_file",
        classmethod(fake_from_authorized_user_file),
    )

    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        oauth_client_secret_path=str(tmp_path / "client-secret.json"),
        token_path=str(token_file),
    )
    monkeypatch.setattr(adapter, "_build_service", lambda credentials: credentials)

    credentials = adapter._build_gmail_service()

    assert isinstance(credentials, FakeCredentials)
    assert loaded == {
        "path": str(token_file),
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    }


def test_gmail_adapter_refreshes_expired_oauth_token(tmp_path, monkeypatch) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("{}", encoding="utf-8")

    class FakeCredentials:
        expired = True
        refresh_token = "refresh-token"
        valid = False
        refreshed = False

        def refresh(self, request: object) -> None:
            self.refreshed = True
            self.expired = False
            self.valid = True

        def to_json(self) -> str:
            return '{"token": "new-token"}'

    fake_credentials = FakeCredentials()

    from google.oauth2.credentials import Credentials

    monkeypatch.setattr(
        Credentials,
        "from_authorized_user_file",
        classmethod(lambda cls, path, scopes: fake_credentials),
    )

    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        oauth_client_secret_path=str(tmp_path / "client-secret.json"),
        token_path=str(token_file),
    )
    monkeypatch.setattr(adapter, "_build_service", lambda credentials: credentials)

    credentials = adapter._build_gmail_service()

    assert credentials is fake_credentials
    assert fake_credentials.refreshed is True
    assert token_file.read_text(encoding="utf-8") == '{"token": "new-token"}'


def test_gmail_adapter_returns_empty_when_oauth_token_is_missing(tmp_path) -> None:
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        oauth_client_secret_path=str(tmp_path / "client-secret.json"),
        token_path=str(tmp_path / "missing-token.json"),
    )

    assert adapter.fetch_emails() == []
    assert adapter.last_fetch_succeeded is False


def test_linkedin_sender_passes_filter() -> None:
    raw_email = RawEmail(
        subject="Maya Lee posted an update",
        sender="notifications-noreply@linkedin.com",
        snippet="Maya posted",
        body="Maya shared a new research update.",
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is True


def test_linkedin_subject_passes_filter() -> None:
    raw_email = RawEmail(
        subject="Maya Lee posted on LinkedIn",
        sender="updates@example.edu",
        snippet="Maya posted",
        body="Maya shared a new research update.",
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is True


def test_linkedin_body_url_passes_filter() -> None:
    raw_email = RawEmail(
        subject="Maya Lee posted an update",
        sender="updates@example.edu",
        snippet="Maya posted",
        body="Read more at https://www.linkedin.com/feed/update/urn:li:activity:123",
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is True


def test_newsletter_email_is_filtered_out() -> None:
    raw_email = RawEmail(
        subject="Research Matters",
        sender="newsletter@example.edu",
        snippet="This week's research news",
        body=(
            "Faculty shared new publications, posted updates, and refreshed profile pages "
            "in this week's campus research roundup."
        ),
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is False
    assert is_likely_ub_cse_activity_email(raw_email) is False


def test_ub_cse_research_email_passes_relevance_filter() -> None:
    raw_email = RawEmail(
        subject="Research Matters: UB CSE faculty receive new funding",
        sender="news@buffalo.edu",
        snippet="University at Buffalo research update",
        body=(
            "University at Buffalo Department of Computer Science and Engineering "
            "faculty received research funding for a new AI project."
        ),
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is False
    assert is_likely_ub_cse_activity_email(raw_email) is True


def test_linkedin_news_email_is_not_faculty_activity() -> None:
    raw_email = RawEmail(
        subject="LinkedIn News: Airlines face delays",
        sender="LinkedIn News <editors-noreply@linkedin.com>",
        snippet="Suggested top conversations",
        body=(
            "See the story. Gain more insights on this developing story "
            "about airline travel."
        ),
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is True
    assert is_likely_faculty_activity_email(raw_email) is False


def test_normal_linkedin_notification_is_faculty_activity_candidate() -> None:
    raw_email = RawEmail(
        subject="Maya Lee shared an update",
        sender="LinkedIn <notifications-noreply@linkedin.com>",
        snippet="Maya shared an update",
        body="Maya shared a new project: https://www.linkedin.com/feed/update/urn:li:activity:123",
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is True
    assert is_likely_faculty_activity_email(raw_email) is True
    assert is_relevant_activity_email(raw_email) is True


def test_linkedin_invitation_email_is_not_relevant_activity() -> None:
    raw_email = RawEmail(
        subject="Maya Lee sent you an invitation",
        sender="LinkedIn <invitations@linkedin.com>",
        snippet="Maya Lee is waiting for your response",
        body=(
            "I want to connect with you on LinkedIn. Accept: "
            "https://www.linkedin.com/in/maya-lee View profile: "
            "https://www.linkedin.com/in/maya-lee"
        ),
        received_at=datetime.now(timezone.utc),
    )

    assert is_likely_linkedin_email(raw_email) is True
    assert is_relevant_activity_email(raw_email) is False


class FakeGmailRequest:
    def __init__(self, response: dict) -> None:
        self.response = response

    def execute(self) -> dict:
        return self.response


class FakeGmailMessages:
    def __init__(self, list_response: dict, full_messages: dict[str, dict]) -> None:
        self.list_response = list_response
        self.full_messages = full_messages
        self.list_calls: list[dict] = []
        self.get_calls: list[dict] = []

    def list(self, **kwargs) -> FakeGmailRequest:
        self.list_calls.append(kwargs)
        return FakeGmailRequest(self.list_response)

    def get(self, **kwargs) -> FakeGmailRequest:
        self.get_calls.append(kwargs)
        return FakeGmailRequest(self.full_messages[kwargs["id"]])


class FakeGmailUsers:
    def __init__(self, messages_resource: FakeGmailMessages) -> None:
        self.messages_resource = messages_resource

    def messages(self) -> FakeGmailMessages:
        return self.messages_resource


class FakeGmailService:
    def __init__(self, messages_resource: FakeGmailMessages) -> None:
        self.messages_resource = messages_resource

    def users(self) -> FakeGmailUsers:
        return FakeGmailUsers(self.messages_resource)


def test_gmail_adapter_fetches_full_messages_and_returns_raw_emails() -> None:
    full_message = {
        "id": "gmail-message-1",
        "snippet": "Snippet fallback",
        "internalDate": "1714492800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Prof Maya Lee shared an update"},
                {"name": "From", "value": "LinkedIn <notifications-noreply@linkedin.com>"},
            ],
            "body": {"data": _base64url("Plain text Gmail body")},
            "mimeType": "text/plain",
        },
    }
    messages_resource = FakeGmailMessages(
        list_response={"messages": [{"id": "gmail-message-1"}]},
        full_messages={"gmail-message-1": full_message},
    )
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        service_builder=lambda: FakeGmailService(messages_resource),
    )

    records = adapter.fetch_emails()

    assert len(records) == 1
    assert records[0].subject == "Prof Maya Lee shared an update"
    assert records[0].body == "Plain text Gmail body"
    assert messages_resource.list_calls == [{"userId": "me", "q": "from:linkedin.com", "maxResults": 10}]
    assert messages_resource.get_calls == [{"userId": "me", "id": "gmail-message-1", "format": "full"}]


def test_gmail_adapter_adds_after_query_when_cursor_exists() -> None:
    full_message = {
        "id": "gmail-message-1",
        "snippet": "Snippet fallback",
        "internalDate": "1714492800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Prof Maya Lee shared an update"},
                {"name": "From", "value": "LinkedIn <notifications-noreply@linkedin.com>"},
            ],
            "body": {"data": _base64url("Plain text Gmail body")},
            "mimeType": "text/plain",
        },
    }
    messages_resource = FakeGmailMessages(
        list_response={"messages": [{"id": "gmail-message-1"}]},
        full_messages={"gmail-message-1": full_message},
    )
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        received_after=datetime(2026, 4, 27, 15, 30, tzinfo=timezone.utc),
        service_builder=lambda: FakeGmailService(messages_resource),
    )

    records = adapter.fetch_emails()

    assert len(records) == 1
    assert messages_resource.list_calls == [
        {"userId": "me", "q": "from:linkedin.com after:2026/04/27", "maxResults": 10}
    ]


def test_gmail_adapter_filters_non_linkedin_messages_before_returning_raw_emails() -> None:
    newsletter = {
        "id": "gmail-message-1",
        "snippet": "Campus research newsletter",
        "internalDate": "1714492800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Research Matters"},
                {"name": "From", "value": "newsletter@example.edu"},
            ],
            "body": {"data": _base64url("A weekly roundup of campus research stories.")},
            "mimeType": "text/plain",
        },
    }
    messages_resource = FakeGmailMessages(
        list_response={"messages": [{"id": "gmail-message-1"}]},
        full_messages={"gmail-message-1": newsletter},
    )
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        service_builder=lambda: FakeGmailService(messages_resource),
    )

    assert adapter.fetch_emails() == []


def test_gmail_adapter_keeps_ub_cse_research_messages_before_returning_raw_emails() -> None:
    ub_research = {
        "id": "gmail-message-1",
        "snippet": "University at Buffalo research update",
        "internalDate": "1714492800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Research Matters: UB CSE faculty receive new funding"},
                {"name": "From", "value": "news@buffalo.edu"},
            ],
            "body": {
                "data": _base64url(
                    "University at Buffalo Department of Computer Science and Engineering "
                    "faculty received research funding for a new AI project."
                )
            },
            "mimeType": "text/plain",
        },
    }
    messages_resource = FakeGmailMessages(
        list_response={"messages": [{"id": "gmail-message-1"}]},
        full_messages={"gmail-message-1": ub_research},
    )
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        service_builder=lambda: FakeGmailService(messages_resource),
    )

    records = adapter.fetch_emails()

    assert len(records) == 1
    assert records[0].subject == "Research Matters: UB CSE faculty receive new funding"


def test_gmail_adapter_filters_linkedin_news_messages_before_returning_raw_emails() -> None:
    linkedin_news = {
        "id": "gmail-message-1",
        "snippet": "Suggested top conversations",
        "internalDate": "1714492800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "LinkedIn News: Airlines face delays"},
                {"name": "From", "value": "LinkedIn News <editors-noreply@linkedin.com>"},
            ],
            "body": {
                "data": _base64url(
                    "See the story. Gain more insights on this developing story."
                )
            },
            "mimeType": "text/plain",
        },
    }
    messages_resource = FakeGmailMessages(
        list_response={"messages": [{"id": "gmail-message-1"}]},
        full_messages={"gmail-message-1": linkedin_news},
    )
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        service_builder=lambda: FakeGmailService(messages_resource),
    )

    assert adapter.fetch_emails() == []


def test_gmail_adapter_filters_linkedin_invitation_messages_before_returning_raw_emails() -> None:
    invitation = {
        "id": "gmail-message-1",
        "snippet": "Maya Lee is waiting for your response",
        "internalDate": "1714492800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Maya Lee sent you an invitation"},
                {"name": "From", "value": "LinkedIn <invitations@linkedin.com>"},
            ],
            "body": {
                "data": _base64url(
                    "I want to connect with you on LinkedIn. Accept: "
                    "https://www.linkedin.com/in/maya-lee View profile: "
                    "https://www.linkedin.com/in/maya-lee"
                )
            },
            "mimeType": "text/plain",
        },
    }
    messages_resource = FakeGmailMessages(
        list_response={"messages": [{"id": "gmail-message-1"}]},
        full_messages={"gmail-message-1": invitation},
    )
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        service_builder=lambda: FakeGmailService(messages_resource),
    )

    assert adapter.fetch_emails() == []


def test_gmail_adapter_fetch_returns_empty_when_list_has_no_messages() -> None:
    messages_resource = FakeGmailMessages(list_response={}, full_messages={})
    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        service_builder=lambda: FakeGmailService(messages_resource),
    )

    assert adapter.fetch_emails() == []
    assert adapter.last_fetch_succeeded is True
    assert messages_resource.get_calls == []


def test_gmail_adapter_fetch_returns_empty_when_service_creation_fails() -> None:
    def failing_service_builder() -> None:
        raise RuntimeError("missing credentials")

    adapter = GmailAPIIngestionAdapter(
        query="from:linkedin.com",
        max_results=10,
        service_builder=failing_service_builder,
    )

    assert adapter.fetch_emails() == []


def test_gmail_adapter_maps_full_fake_message_to_raw_email() -> None:
    adapter = GmailAPIIngestionAdapter(query="from:linkedin.com", max_results=10)
    message = {
        "id": "gmail-message-1",
        "snippet": "Snippet fallback",
        "internalDate": "1714492800000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Prof Maya Lee shared an update"},
                {"name": "From", "value": "LinkedIn <notifications-noreply@linkedin.com>"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": _base64url(
                            "Prof Maya Lee shared an update\n"
                            "https://www.linkedin.com/feed/update/urn:li:activity:123"
                        )
                    },
                },
                {"mimeType": "text/html", "body": {"data": _base64url("<p>HTML update</p>")}},
            ],
        },
    }

    records = adapter.convert_messages([message])

    assert len(records) == 1
    assert records[0].subject == "Prof Maya Lee shared an update"
    assert records[0].sender == "LinkedIn <notifications-noreply@linkedin.com>"
    assert records[0].snippet == "Snippet fallback"
    assert "linkedin.com/feed/update" in records[0].body
    assert records[0].received_at.isoformat() == "2024-04-30T16:00:00+00:00"


def test_gmail_adapter_decodes_base64url_text_plain_body() -> None:
    adapter = GmailAPIIngestionAdapter(query="from:linkedin.com", max_results=10)
    message = {
        "snippet": "Snippet fallback",
        "payload": {
            "headers": [],
            "body": {"data": _base64url("Plain text body with linkedin.com link")},
            "mimeType": "text/plain",
        },
    }

    records = adapter.convert_messages([message])

    assert records[0].body == "Plain text body with linkedin.com link"


def test_gmail_adapter_falls_back_to_snippet_when_body_is_missing() -> None:
    adapter = GmailAPIIngestionAdapter(query="from:linkedin.com", max_results=10)
    message = {
        "snippet": "Use this snippet",
        "payload": {
            "headers": [{"name": "Subject", "value": "LinkedIn Update"}],
        },
    }

    records = adapter.convert_messages([message])

    assert records[0].body == "Use this snippet"


def test_gmail_adapter_handles_missing_headers_without_crashing() -> None:
    adapter = GmailAPIIngestionAdapter(query="from:linkedin.com", max_results=10)
    message = {
        "snippet": "LinkedIn notification",
        "payload": {
            "body": {"data": "not valid base64url"},
            "mimeType": "text/plain",
        },
    }

    records = adapter.convert_messages([message])

    assert len(records) == 1
    assert records[0].subject == ""
    assert records[0].sender == ""
    assert records[0].body == "LinkedIn notification"


def test_gmail_adapter_handles_empty_message_list() -> None:
    adapter = GmailAPIIngestionAdapter(query="from:linkedin.com", max_results=10)

    assert adapter.convert_messages([]) == []
