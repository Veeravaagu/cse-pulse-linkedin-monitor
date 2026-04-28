from app.models.schemas import ActivityCategory, EnrichedActivity, ParsedEmailActivity, ReviewStatus


class MockProcessor:
    """Rule-based enrichment used for local development and tests.

    Beginner note:
    - This keeps the current heuristic behavior working without any API calls.
    - Later we can swap in a real LLM processor without changing route logic.
    """

    CATEGORY_RULES: dict[ActivityCategory, tuple[str, ...]] = {
        ActivityCategory.award: ("award", "honor", "winner"),
        ActivityCategory.grant: ("grant", "funded", "grant-funded"),
        ActivityCategory.publication: ("publication", "paper", "journal"),
        ActivityCategory.talk_event: ("talk", "seminar", "keynote", "event", "conference", "workshop"),
        ActivityCategory.faculty_student: ("student", "mentored", "achievement"),
        ActivityCategory.department_news: ("department news", "department update", "cse news"),
        ActivityCategory.funding_opportunity: ("funding opportunity", "applications due", "apply by"),
        ActivityCategory.research: ("research project", "research update", "study"),
    }

    def enrich(self, parsed: ParsedEmailActivity) -> EnrichedActivity:
        category = self._classify(parsed)
        summary = self._summarize(parsed.raw_text)
        priority = self._priority(category)

        return EnrichedActivity(
            ai_summary=summary,
            category=category,
            priority=priority,
            review_status=ReviewStatus.pending,
        )

    def _classify(self, parsed: ParsedEmailActivity) -> ActivityCategory:
        lowered = parsed.raw_text.lower()
        if parsed.source_type == "ub_cse_email" and "research matters" in lowered:
            return ActivityCategory.other

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
        medium_priority = {
            ActivityCategory.research,
            ActivityCategory.talk_event,
            ActivityCategory.faculty_student,
            ActivityCategory.department_news,
            ActivityCategory.funding_opportunity,
        }

        if category in high_priority:
            return 5
        if category in medium_priority:
            return 3
        return 2
