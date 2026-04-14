from app.config import settings
from app.services.enrichment.base import EnrichmentProcessor
from app.services.enrichment.llm_processor import LLMProcessor
from app.services.enrichment.mock_processor import MockProcessor


def build_enrichment_processor(provider: str | None = None) -> EnrichmentProcessor:
    """Build an enrichment processor from config.

    If provider is omitted we use settings.ai_provider.
    Supported values: "mock", "llm".
    """

    selected_provider = (provider or settings.ai_provider).strip().lower()

    if selected_provider == "llm":
        return LLMProcessor(model=settings.ai_model)
    if selected_provider == "mock":
        return MockProcessor()

    raise ValueError(f"Unsupported ai_provider '{selected_provider}'. Expected 'mock' or 'llm'.")
