import re

from app.models.schemas import ActivityCategory, EnrichedActivity, ParsedEmailActivity, ReviewStatus

FORWARD_PREFIX_PATTERN = re.compile(r"^(?:(?:fw|fwd|re):\s*)+", re.IGNORECASE)


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

    BOILERPLATE_MARKERS = (
        "research matters:",
        "in this issue:",
        "updates from research, innovation and economic development",
        "copyright",
        "unsubscribe",
        "all rights reserved",
    )

    HEADLINE_MARKERS = (
        "seminar",
        "workshop",
        "talk",
        "conference",
        "grant",
        "award",
        "publication",
        "paper",
        "funding",
        "applications due",
        "apply by",
    )

    def enrich(self, parsed: ParsedEmailActivity) -> EnrichedActivity:
        category = self._classify(parsed)
        if parsed.source_type == "ub_cse_email" and parsed.faculty_name is None:
            parsed.faculty_name = self._extract_headline(parsed.raw_text)
        summary = self._summarize(parsed.raw_text)
        priority = self._priority(category)

        return EnrichedActivity(
            ai_summary=summary,
            category=category,
            priority=priority,
            review_status=ReviewStatus.pending,
        )

    def _classify(self, parsed: ParsedEmailActivity) -> ActivityCategory:
        activity_text = self._activity_text(parsed.raw_text)
        lowered = activity_text.lower()
        if not lowered and parsed.source_type == "ub_cse_email" and "research matters" in parsed.raw_text.lower():
            return ActivityCategory.other
        if parsed.source_type == "ub_cse_email" and "newsletter" in lowered:
            return ActivityCategory.other

        for category, keywords in self.CATEGORY_RULES.items():
            if any(keyword in lowered for keyword in keywords):
                return category
        return ActivityCategory.other

    @classmethod
    def _summarize(cls, text: str, max_len: int = 220) -> str:
        compact = cls._activity_text(text)
        if len(compact) <= max_len:
            return compact
        return f"{compact[: max_len - 3]}..."

    @classmethod
    def _activity_text(cls, text: str, max_lines: int = 2) -> str:
        lines = cls._candidate_lines(text)
        if not lines:
            return " ".join(cls._clean_line(text).split())

        selected = lines[:max_lines]
        sentences = [cls._as_sentence(line) for line in selected]
        return " ".join(sentences)

    @classmethod
    def _extract_headline(cls, text: str) -> str | None:
        for line in cls._candidate_lines(text):
            lowered = line.lower()
            if len(line) <= 90 and any(marker in lowered for marker in cls.HEADLINE_MARKERS):
                return line.rstrip(".")
        return None

    @classmethod
    def _candidate_lines(cls, text: str) -> list[str]:
        lines: list[str] = []
        for raw_line in text.splitlines():
            line = cls._clean_line(raw_line)
            if not line or cls._is_boilerplate(line):
                continue
            lines.append(line)
        return lines

    @staticmethod
    def _clean_line(line: str) -> str:
        return FORWARD_PREFIX_PATTERN.sub("", line).strip(" -\t")

    @classmethod
    def _is_boilerplate(cls, line: str) -> bool:
        lowered = line.lower()
        return any(marker in lowered for marker in cls.BOILERPLATE_MARKERS)

    @staticmethod
    def _as_sentence(line: str) -> str:
        return line if line.endswith((".", "!", "?")) else f"{line}."

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
