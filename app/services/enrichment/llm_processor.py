from app.models.schemas import EnrichedActivity, ParsedEmailActivity


class LLMProcessor:
    """Placeholder for future LLM-backed enrichment.

    Beginner note:
    - The class exists now so config and routing can already target an LLM mode.
    - The actual model call is intentionally not implemented in this milestone.
    """

    def __init__(self, model: str):
        self.model = model

    def enrich(self, parsed: ParsedEmailActivity) -> EnrichedActivity:
        """Scaffold-only implementation.

        TODO:
        - Add provider client initialization
        - Prompt the model for category / summary / priority
        - Validate and normalize model output into EnrichedActivity
        """

        raise NotImplementedError(
            f"LLM enrichment is not implemented yet for model '{self.model}'. "
            "Use ai_provider='mock' for local development."
        )
