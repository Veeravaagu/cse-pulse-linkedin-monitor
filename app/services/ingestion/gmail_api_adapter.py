import logging

from app.models.schemas import RawEmail

logger = logging.getLogger(__name__)


class GmailAPIIngestionAdapter:
    """Scaffold for future Gmail API ingestion.

    Safe placeholder behavior:
    - does not authenticate
    - does not call Google APIs
    - returns an empty batch
    """

    def __init__(self, query: str, max_results: int) -> None:
        self.query = query
        self.max_results = max_results

    def fetch_emails(self) -> list[RawEmail]:
        # TODO(milestone-3): Implement OAuth/service-account auth and Gmail API calls.
        # TODO(milestone-3): Convert Gmail message payloads into RawEmail schema.
        logger.info(
            "GmailAPIIngestionAdapter is scaffold-only. query=%s, max_results=%s",
            self.query,
            self.max_results,
        )
        return []
