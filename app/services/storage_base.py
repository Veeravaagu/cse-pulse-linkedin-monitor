from typing import Protocol

from app.models.schemas import ActivityCategory, ActivityRecord, EnrichedActivity, ParsedEmailActivity, ReviewStatus


class ActivityStorage(Protocol):
    """Common interface for storage backends.

    Beginner note:
    - The API and ingestion flow should depend on this contract, not on a
      specific JSON implementation.
    - That makes it easier to add SQLite later without rewriting route logic.
    """

    def list_all(self) -> list[ActivityRecord]:
        """Return every stored activity."""

    def list_activities(
        self,
        *,
        category: ActivityCategory | None = None,
        review_status: ReviewStatus | None = None,
        sort_by: str = "detected_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int | None = None,
        days: int | None = None,
    ) -> list[ActivityRecord]:
        """Return activities with optional filtering, sorting, and pagination."""

    def get_by_id(self, record_id: str) -> ActivityRecord | None:
        """Return a single activity, or None if missing."""

    def update_review_status(self, record_id: str, review_status: ReviewStatus) -> ActivityRecord | None:
        """Persist a review status change, or return None if missing."""

    def delete_rejected(self, record_id: str) -> bool:
        """Delete a rejected activity, returning whether anything was removed."""

    def delete_rejected_many(self, record_ids: list[str]) -> int:
        """Delete rejected activities by ID, returning the number removed."""

    def list_high_priority(self, threshold: int = 4) -> list[ActivityRecord]:
        """Return activities whose priority is at or above the threshold."""

    def exists_by_source_url(self, source_url: str) -> bool:
        """Return whether an activity with this source URL already exists."""

    def create(self, parsed: ParsedEmailActivity, enriched: EnrichedActivity) -> ActivityRecord:
        """Persist one parsed + enriched activity and return the saved row."""
