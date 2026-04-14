from app.services.enrichment.mock_processor import MockProcessor


class AIProcessor(MockProcessor):
    """Compatibility shim for older imports.

    New code should import MockProcessor from app.services.enrichment instead.
    """
