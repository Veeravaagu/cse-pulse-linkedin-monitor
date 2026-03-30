from typing import Protocol

from app.models.schemas import RawEmail


class GmailIngestionAdapter(Protocol):
    """Common interface for all Gmail ingestion implementations.

    Beginner note:
    - "adapter" means a thin wrapper around a data source.
    - every adapter returns RawEmail objects, so parsing/enrichment code does not
      need to care if data came from a JSON file or Gmail API.
    """

    def fetch_emails(self) -> list[RawEmail]:
        """Load the next batch of Gmail-style notifications."""
