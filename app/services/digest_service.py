from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from app.models.schemas import ActivityCategory, ActivityRecord, ReviewStatus
from app.services.storage_base import ActivityStorage


class DigestService:
    """Build a simple digest preview from stored activity records.

    Beginner note:
    - This service reads from the storage interface, so it does not care whether
      records come from JSON today or a database later.
    - The output is plain text so it is easy to preview in a browser or demo.
    """

    def __init__(self, storage: ActivityStorage):
        self.storage = storage

    def generate_preview(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        review_status: ReviewStatus | None = None,
    ) -> str:
        digest = self.generate_structured(
            start_date=start_date,
            end_date=end_date,
            review_status=review_status,
        )

        lines = [
            "# Weekly Activity Digest",
            f"Date range: {digest['date_range']['start_date']} to {digest['date_range']['end_date']}",
            f"Review status: {digest['review_status']}",
            f"Total items: {digest['total_items']}",
            "",
        ]

        if not digest["sections"]:
            lines.append("No activities matched this digest window.")
            return "\n".join(lines)

        for section in digest["sections"]:
            lines.append(f"## {section['category_label']}")
            for item in section["items"]:
                lines.append(
                    f"- [P{item['priority']}] {item['faculty_name']} ({item['detected_at'][:10]}): {item['ai_summary']}"
                )
            lines.append("")

        return "\n".join(lines).rstrip()

    def generate_structured(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        review_status: ReviewStatus | None = None,
        max_items_per_category: int | None = None,
    ) -> dict[str, object]:
        """Build a structured digest payload for APIs or future exports."""

        window_start, window_end = self._resolve_window(start_date=start_date, end_date=end_date)
        records = self.storage.list_activities(
            review_status=review_status,
            sort_by="detected_at",
            sort_order="desc",
        )
        records = [item for item in records if window_start <= item.detected_at <= window_end]
        grouped = self._group_records(records)

        sections: list[dict[str, object]] = []
        for category in ActivityCategory:
            items = grouped.get(category, [])
            if not items:
                continue

            if max_items_per_category is not None:
                items = items[:max_items_per_category]

            sections.append(
                {
                    "category": category.value,
                    "category_label": self._format_category_name(category),
                    "item_count": len(items),
                    "items": [self._serialize_item(item) for item in items],
                }
            )

        return {
            "date_range": {
                "start_date": window_start.date().isoformat(),
                "end_date": window_end.date().isoformat(),
            },
            "review_status": review_status.value if review_status else "all",
            "total_items": len(records),
            "sections": sections,
        }

    def generate_markdown_export(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        review_status: ReviewStatus | None = None,
        max_items_per_category: int | None = None,
        include_section_totals: bool = False,
        summary_max_length: int | None = None,
    ) -> str:
        """Build a delivery-friendly Markdown digest without changing preview output."""

        digest = self.generate_structured(
            start_date=start_date,
            end_date=end_date,
            review_status=review_status,
            max_items_per_category=max_items_per_category,
        )

        lines = [
            "# Weekly Activity Digest",
            f"- Date range: {digest['date_range']['start_date']} to {digest['date_range']['end_date']}",
            f"- Review status: {digest['review_status']}",
            f"- Total items: {digest['total_items']}",
            "",
        ]

        if not digest["sections"]:
            lines.append("No activities matched this digest window.")
            return "\n".join(lines)

        for section in digest["sections"]:
            heading = f"## {section['category_label']}"
            if include_section_totals:
                heading = f"{heading} ({section['item_count']})"

            lines.append(heading)
            for item in section["items"]:
                summary = self._truncate_summary(item["ai_summary"], summary_max_length)
                lines.append(
                    f"- [P{item['priority']}] {item['faculty_name']} ({item['detected_at'][:10]}): {summary}"
                )
            lines.append("")

        return "\n".join(lines).rstrip()

    @staticmethod
    def _resolve_window(
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)

        if start_date is None and end_date is None:
            return now - timedelta(days=7), now

        if end_date is None:
            end_date = now.date()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        end_at = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        return start_at, end_at

    @staticmethod
    def _group_records(records: list[ActivityRecord]) -> dict[ActivityCategory, list[ActivityRecord]]:
        grouped: dict[ActivityCategory, list[ActivityRecord]] = defaultdict(list)

        for item in records:
            grouped[item.category].append(item)

        for items in grouped.values():
            items.sort(key=lambda item: (item.priority, item.detected_at), reverse=True)

        return grouped

    @staticmethod
    def _format_category_name(category: ActivityCategory) -> str:
        return category.value.replace("_", " ").title()

    @staticmethod
    def _serialize_item(item: ActivityRecord) -> dict[str, object]:
        return {
            "id": item.id,
            "faculty_name": item.faculty_name or "General CSE activity",
            "ai_summary": item.ai_summary,
            "priority": item.priority,
            "detected_at": item.detected_at.isoformat(),
            "review_status": item.review_status.value,
            "source_url": item.source_url,
        }

    @staticmethod
    def _truncate_summary(summary: str, max_length: int | None) -> str:
        if max_length is None or len(summary) <= max_length:
            return summary
        if max_length <= 3:
            return summary[:max_length]
        return f"{summary[: max_length - 3]}..."
