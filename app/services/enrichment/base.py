from typing import Protocol

from app.models.schemas import EnrichedActivity, ParsedEmailActivity


class EnrichmentProcessor(Protocol):
    """Common interface for all enrichment implementations.

    Beginner note:
    - A "processor" takes parsed text and returns a schema-validated enrichment.
    - The rest of the app should only depend on this contract, not on a specific
      mock or LLM implementation.
    """

    def enrich(self, parsed: ParsedEmailActivity) -> EnrichedActivity:
        """Generate category, summary, priority, and review status."""
