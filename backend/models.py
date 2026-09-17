import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String, nullable=False)
    subscription_status = Column(String, nullable=False)
    revenuecat_user_id = Column(String, nullable=True)
    expo_push_token = Column(String, nullable=True)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    raw_paragraph = Column(String, nullable=False)
    search_queries = Column(ARRAY(String), nullable=False)
    thematic_tags = Column(ARRAY(String), nullable=False)
    tone_bucket = Column(String, nullable=False)
    tone_freeform = Column(String, nullable=True)
    exclude_keywords = Column(ARRAY(String), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)

class LLMCallLog(Base):
    __tablename__ = "llm_call_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

class NewsCluster(Base):
    __tablename__ = "news_clusters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_date = Column(Date, nullable=False)
    canonical_title = Column(String, nullable=False)
    representative_snippet = Column(String, nullable=False)
    source_count = Column(Integer, nullable=False)
    matched_tags = Column(ARRAY(String), nullable=False)
    article_refs = Column(JSONB, nullable=False)

    __table_args__ = (
        Index("ix_news_clusters_batch_date", "batch_date"),
    )

class Card(Base):
    __tablename__ = "cards"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("news_clusters.id"), nullable=False)
    tone_bucket = Column(String, nullable=False)
    headline = Column(String, nullable=False)
    bullets = Column(ARRAY(String), nullable=False)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("cluster_id", "tone_bucket", name="uq_card_cluster_tone"),
    )

class SuperSummary(Base):
    __tablename__ = "super_summaries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_date = Column(Date, nullable=False)
    cluster_set_key = Column(String, nullable=False)
    tone_bucket = Column(String, nullable=False)
    headline = Column(String, nullable=False)
    synthesis = Column(String, nullable=False)
    contributing_cluster_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)

    __table_args__ = (
        UniqueConstraint("cluster_set_key", "tone_bucket", name="uq_super_summary_cluster_set_tone"),
    )

class DeepDive(Base):
    __tablename__ = "deep_dives"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("news_clusters.id"), unique=True, nullable=False)
    title = Column(String, nullable=False)
    body_markdown = Column(String, nullable=False)
    pre_generated = Column(Boolean, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False)

class UserBriefing(Base):
    __tablename__ = "user_briefings"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    batch_date = Column(Date, primary_key=True)
    super_summary_id = Column(UUID(as_uuid=True), ForeignKey("super_summaries.id"), nullable=True)
    card_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)

class DailyCardUsage(Base):
    __tablename__ = "daily_card_usage"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    date = Column(Date, primary_key=True)
    cards_viewed_count = Column(Integer, nullable=False, default=0)

class CardViewLog(Base):
    __tablename__ = "card_view_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    card_id = Column(UUID(as_uuid=True))
    viewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
