from app.config import settings
from datetime import datetime
from app.services.ingestion.base import GmailIngestionAdapter
from app.services.ingestion.gmail_api_adapter import GmailAPIIngestionAdapter
from app.services.ingestion.mock_adapter import MockGmailIngestionAdapter


def build_ingestion_adapter(mode: str | None = None, received_after: datetime | None = None) -> GmailIngestionAdapter:
    """Build an ingestion adapter from config.

    If mode is omitted we use settings.ingestion_mode.
    Supported values: "mock", "gmail".
    """

    selected_mode = (mode or settings.ingestion_mode).strip().lower()

    if selected_mode == "gmail":
        return GmailAPIIngestionAdapter(
            query=settings.gmail_query,
            max_results=settings.gmail_max_results,
            credentials_path=settings.gmail_credentials_path,
            received_after=received_after,
        )

    if selected_mode == "mock":
        return MockGmailIngestionAdapter(payload_path=settings.mock_email_payload_path)

    raise ValueError(f"Unsupported ingestion_mode '{selected_mode}'. Expected 'mock' or 'gmail'.")
