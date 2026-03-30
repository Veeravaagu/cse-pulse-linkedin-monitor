"""Ingestion adapter package.

This package hides *where* email notifications come from so the rest of the
pipeline can stay the same (parser -> AI -> storage).
"""

from app.services.ingestion.base import GmailIngestionAdapter
from app.services.ingestion.factory import build_ingestion_adapter
from app.services.ingestion.gmail_api_adapter import GmailAPIIngestionAdapter
from app.services.ingestion.mock_adapter import MockGmailIngestionAdapter

__all__ = [
    "GmailIngestionAdapter",
    "MockGmailIngestionAdapter",
    "GmailAPIIngestionAdapter",
    "build_ingestion_adapter",
]
