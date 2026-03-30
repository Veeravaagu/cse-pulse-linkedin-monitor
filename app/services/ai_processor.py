from app.models.schemas import ActivityCategory, EnrichedActivity, ParsedEmailActivity, ReviewStatus


class AIProcessor:
    """Mock AI processor. Later replace internals with an LLM call."""

    CATEGORY_RULES: dict[ActivityCategory, tuple[str, ...]] = {
        ActivityCategory.publication: ("publication", "paper", "journal"),
        ActivityCategory.grant: ("grant", "funded", "funding"),
        ActivityCategory.talk: ("talk", "seminar", "keynote"),
        ActivityCategory.award: ("award", "honor", "winner"),
        ActivityCategory.event: ("event", "conference", "workshop"),
        ActivityCategory.student_achievement: ("student", "mentored", "achievement"),
    }

    def enrich(self, parsed: ParsedEmailActivity) -> EnrichedActivity:
        category = self._classify(parsed.raw_text)
        summary = self._summarize(parsed.raw_text)
        priority = self._priority(category)

        return EnrichedActivity(
            ai_summary=summary,
            category=category,
            priority=priority,
            review_status=ReviewStatus.pending,
        )

    def _classify(self, text: str) -> ActivityCategory:
        lowered = text.lower()
        for category, keywords in self.CATEGORY_RULES.items():
            if any(keyword in lowered for keyword in keywords):
                return category
        return ActivityCategory.other

    @staticmethod
    def _summarize(text: str, max_len: int = 160) -> str:
        compact = " ".join(text.split())
        if len(compact) <= max_len:
            return compact
        return f"{compact[: max_len - 3]}..."

    @staticmethod
    def _priority(category: ActivityCategory) -> int:
        high_priority = {ActivityCategory.grant, ActivityCategory.award, ActivityCategory.publication}
        medium_priority = {ActivityCategory.talk, ActivityCategory.event, ActivityCategory.student_achievement}

        if category in high_priority:
            return 5
        if category in medium_priority:
            return 3
        return 2
