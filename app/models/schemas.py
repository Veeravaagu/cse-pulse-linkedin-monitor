from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ActivityCategory(str, Enum):
    research = "research"
    award = "award"
    grant = "grant"
    publication = "publication"
    talk_event = "talk_event"
    faculty_student = "faculty_student"
    department_news = "department_news"
    funding_opportunity = "funding_opportunity"
    other = "other"


class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    reviewed = "reviewed"


class RawEmail(BaseModel):
    """Represents a minimal Gmail notification payload used by this module."""

    subject: str
    sender: str
    snippet: str
    body: str = ""
    received_at: datetime


class ParsedEmailActivity(BaseModel):
    faculty_name: str | None = None
    source_type: str = "linkedin_email"
    source_url: str | None = None
    raw_text: str
    detected_at: datetime


class EnrichedActivity(BaseModel):
    ai_summary: str
    category: ActivityCategory
    priority: int = Field(ge=1, le=5)
    review_status: ReviewStatus = ReviewStatus.pending


class ActivityRecord(BaseModel):
    id: str
    faculty_name: str | None = None
    source_type: str = "linkedin_email"
    source_url: str | None = None
    raw_text: str
    ai_summary: str
    category: ActivityCategory
    priority: int = Field(ge=1, le=5)
    detected_at: datetime
    review_status: ReviewStatus = ReviewStatus.pending


class IngestResponse(BaseModel):
    ingested_count: int
    activities: list[ActivityRecord]
