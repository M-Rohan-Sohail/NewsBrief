from pydantic import BaseModel, Field
from typing import List, Optional, Literal

ToneBucket = Literal["high_signal", "technical_deep", "casual", "executive_brief", "default"]

class OnboardingExtractRequest(BaseModel):
    raw_paragraph: str = Field(..., min_length=20, description="User's interest paragraph")

class OnboardingExtractResponse(BaseModel):
    search_queries: List[str]
    thematic_tags: List[str]
    tone_bucket: ToneBucket
    tone_freeform: Optional[str] = None
    exclude_keywords: Optional[List[str]] = []

class OnboardingConfirmRequest(OnboardingExtractResponse):
    raw_paragraph: str

class DeepDiveRequest(BaseModel):
    cluster_id: str

class DeepDiveResponse(BaseModel):
    cluster_id: str
    title: str
    body_markdown: str

class CardResponse(BaseModel):
    id: str
    cluster_id: str
    headline: str
    bullets: List[str]
    source_name: str
    source_url: str

class SuperSummaryResponse(BaseModel):
    id: str
    headline: str
    synthesis: str

class BriefingResponse(BaseModel):
    batch_date: str
    is_preparing_today: bool
    super_summary: SuperSummaryResponse
    cards: List[CardResponse]

class CardViewResponse(BaseModel):
    limit_reached: bool
    views_today: int

from datetime import datetime

class RawArticle(BaseModel):
    id: str
    title: str
    url: str
    source_name: str
    content: str
    published_at: Optional[datetime] = None
    tags: List[str] = []
    author: Optional[str] = None
    score: Optional[int] = 0

class EmailPreferenceResponse(BaseModel):
    daily_digest_enabled: bool
    delivery_time: str

class UpdateEmailPreferenceRequest(BaseModel):
    daily_digest_enabled: Optional[bool] = None
    delivery_time: Optional[str] = None

class AudioResponse(BaseModel):
    audio_url: Optional[str]
    status: str

class FeedbackCreate(BaseModel):
    title: str
    description: str
    category: str = "feature"

class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    category: str
    status: str
    upvotes_count: int
    has_upvoted: bool = False
    created_at: datetime

class FeedbackStatusUpdate(BaseModel):
    status: str

class AnalyticsEventCreate(BaseModel):
    channel: str
    event_name: str
    properties: Optional[dict] = None
