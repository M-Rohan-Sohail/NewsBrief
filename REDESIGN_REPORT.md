# NewsBrief: Comprehensive Architectural Specification & Checkpoint Blueprint

**Document Type:** Exhaustive Engineering Specification & Deterministic Execution Manual  
**Target:** Google Antigravity IDE & StartupX Engineering  
**Version:** 3.0 (Zero-Assumption Edition)  
**Status:** Implementation-Ready  
**Compiled PDF:** [`Redesign Project Report.pdf`](file:///home/rohan/Desktop/StartupX/Redesign%20Project%20Report.pdf)

---

## 1. Architectural Evolution & Operational Principles

### 1.1 The Fundamental Structural Problem
Currently, `backend/run_pipeline.py` runs a quadratic, coupled loop per user:
```text
For each User:
    For each Search Query (5-8 queries):
        Serper.dev News Search (3 links)
        Jina Reader Scrape (3 pages)
    sentence-transformers Deduplication
    Groq LLM Thematic Clustering
    Groq LLM Card Generation
    Groq LLM Super Summary Generation
    Save to DB & Send Push
```
- **Quadratic Scaling Failure:** 1,000 users = 6,000 Serper searches, 18,000 Jina scrapes, 6,000 Groq cluster calls. Instant rate limits, massive latency, and ~$1,500/mo API bills.
- **SEO Spam Fluff:** Serper Google News returns syndicated PR newswires and content-farm blog posts.
- **Single-Channel Churn:** Mobile Push alone suffers from >50% opt-out and high 30-day drop-off.

### 1.2 The Two-Stage Decoupled World-State Architecture
```
STAGE 1: GLOBAL WORLD-STATE INGESTION & CLUSTERING (Daily at 03:00 UTC)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Sources: Hacker News (Firebase), GitHub Trending, arXiv Preprints, Curated Tech RSS    │
│ Pipeline: Ingest All Raw Articles (Pool: ~500) -> Semantic Dedup -> Groq Clustering   │
│ Output: 50–80 Canonical NewsClusters with 384-dim Centroid Embeddings in PostgreSQL    │
│ Pre-generation: Base Cards & Top-10 In-depth Research Deep Dives generated ONCE.       │
└────────────────────────────────────────────────────────────────────────────────────────┘

STAGE 2: PERSONALIZED USER DELIVERY ENGINE (Daily at 06:30 Local User Time)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Vector Match: User Preference Embedding <=> Cluster Embeddings (via pgvector)       │
│ 2. Select: Top 5-7 highest similarity clusters for the individual user                 │
│ 3. Synthesize: User-tailored Super Summary in user's configured tone bucket (1.2s LLM) │
│ 4. Dispatch: Multi-channel delivery to Email Digest, Mobile Push, Audio TTS, Slack Bot │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Zero-Assumption Engineering Checkpoints (CP-16 to CP-25)

### Checkpoint 16: Multi-Source High-Signal Ingestion Engine
- **Objective:** Ingest rich, technical content across developer, preprint, and thought leadership streams.
- **Target Files:**
  - `[NEW] backend/ingestion_sources/__init__.py`
  - `[NEW] backend/ingestion_sources/hn.py` — Hacker News Firebase REST API client.
  - `[NEW] backend/ingestion_sources/github.py` — GitHub Trending repo & release extractor.
  - `[NEW] backend/ingestion_sources/arxiv.py` — arXiv query & XML abstract parser.
  - `[NEW] backend/ingestion_sources/rss.py` — Curated Substack / Tech RSS parser using `feedparser`.
  - `[MODIFY] backend/requirements.txt` — Add `feedparser==6.0.11`, `httpx==0.27.0`.
  - `[MODIFY] backend/schemas.py` — Add `RawArticle` schema.
  - `[NEW] backend/tests/test_ingestion_sources.py` — Unit tests.
- **Data Schema (`backend/schemas.py`):**
  ```python
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
  ```
- **Implementation Guide:**
  - `hn.py`: Call `https://hacker-news.firebaseio.com/v0/topstories.json`. Fetch top 30 stories with score >= 30. Extract text/url.
  - `github.py`: Query GitHub Search API for repos created or active in last 7 days with >100 stars. Ingest readme snippet, language, and star count.
  - `arxiv.py`: Query arXiv API for `cat:cs.AI OR cat:cs.LG OR cat:cs.CL`. Parse XML with `xml.etree.ElementTree`.
  - `rss.py`: Parse 20 curated URLs (Stratechery, SemiAnalysis, Latent Space, etc.) using `feedparser`.
- **Verification:** `pytest backend/tests/test_ingestion_sources.py -v` (Must return >60 unique articles).

---

### Checkpoint 17: Database Schema Migration & `pgvector` Integration
- **Objective:** Equip PostgreSQL with `vector` extension and add relational tables for B2B Teams and Multi-Channel preferences.
- **Target Files:**
  - `[MODIFY] backend/requirements.txt` — Add `pgvector==0.3.6`.
  - `[MODIFY] backend/db.py` — Initialize pgvector support.
  - `[MODIFY] backend/models.py` — Add vector columns and B2B models.
  - `[NEW] backend/alembic/versions/0002_add_pgvector_and_b2b_models.py`
  - `[NEW] backend/tests/test_database_vector.py`
- **Model Changes (`backend/models.py`):**
  ```python
  from pgvector.sqlalchemy import Vector

  # Add to NewsCluster:
  embedding = Column(Vector(384), nullable=True)
  category = Column(String, default="General Tech", nullable=False)

  # Add to UserPreference:
  preference_embedding = Column(Vector(384), nullable=True)

  # Add to SuperSummary:
  audio_url = Column(String, nullable=True)
  audio_duration_seconds = Column(Integer, nullable=True)

  # New Models:
  class Team(Base):
      __tablename__ = "teams"
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      name = Column(String, nullable=False)
      created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
      subscription_status = Column(String, default="active")
      max_seats = Column(Integer, default=15)
      billing_email = Column(String, nullable=True)

  class TeamMembership(Base):
      __tablename__ = "team_memberships"
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
      user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
      role = Column(String, default="member")

  class SlackInstallation(Base):
      __tablename__ = "slack_installations"
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True)
      slack_team_id = Column(String, unique=True, nullable=False)
      slack_team_name = Column(String, nullable=False)
      bot_token = Column(String, nullable=False)
      target_channel_id = Column(String, nullable=False)
      delivery_time_utc = Column(String, default="13:00")
      is_active = Column(Boolean, default=True)

  class UserEmailPreference(Base):
      __tablename__ = "user_email_preferences"
      user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
      email_digest_enabled = Column(Boolean, default=True, nullable=False)
      delivery_hour_utc = Column(Integer, default=11, nullable=False)
      last_sent_at = Column(DateTime(timezone=True), nullable=True)
  ```
- **Verification:** `pytest backend/tests/test_database_vector.py -v` (Validates vector insertion and `<=>` cosine distance search).

---

### Checkpoint 18: Stage 1 Global World-State Pipeline
- **Objective:** Run global daily ingestion, embedding deduplication, Groq clustering, centroid calculation, and pre-generation.
- **Target Files:**
  - `[NEW] backend/pipeline_stage1.py`
  - `[MODIFY] backend/clustering.py` — Add centroid vector calculation (`compute_centroid`).
  - `[MODIFY] backend/generation.py` — Add pre-generation functions for base cards and top 10 Deep Dives.
  - `[NEW] backend/tests/test_pipeline_stage1.py`
- **Execution Logic:**
  1. Aggregate articles across all ingestion sources into `List[RawArticle]` (~400–600 items).
  2. Deduplicate using `SentenceTransformer("all-MiniLM-L6-v2")` with cosine threshold 0.82.
  3. Cluster remaining articles via Groq Qwen into 40–70 canonical clusters.
  4. Compute normalized centroid vector for each cluster and store in `NewsCluster.embedding`.
  5. Pre-generate base cards (tones: `high_signal`, `technical_deep`) and top 10 deep dives.
  6. Upsert everything into PostgreSQL in one atomic transaction.
- **Verification:** `pytest backend/tests/test_pipeline_stage1.py -v`.

---

### Checkpoint 19: Stage 2 User Matching & Personalization Engine
- **Objective:** High-speed personalization matching user vectors against the day's clusters using pgvector (<1.5s/user).
- **Target Files:**
  - `[NEW] backend/pipeline_stage2.py`
  - `[MODIFY] backend/main.py` — Add endpoint `POST /admin/trigger-stage2`.
  - `[NEW] backend/tests/test_pipeline_stage2.py`
- **Implementation:**
  - Compute user preference embedding once if null: `text = f"{raw_paragraph} {' '.join(thematic_tags)} {' '.join(search_queries)}"`.
  - Query DB:
    ```python
    matched = db.query(models.NewsCluster).filter(
        models.NewsCluster.batch_date == today
    ).order_by(
        models.NewsCluster.embedding.cosine_distance(pref.preference_embedding)
    ).limit(6).all()
    ```
  - Synthesize user-specific Super Summary in user's tone bucket.
  - Save `UserBriefing`.
- **Verification:** `pytest backend/tests/test_pipeline_stage2.py -v`.

---

### Checkpoint 20: Daily Email Digest Service (Resend Integration)
- **Objective:** Daily 7:00 AM email digest delivering Super Summary, top 3 cards, and deep dive links.
- **Target Files:**
  - `[MODIFY] backend/requirements.txt` — Add `resend==2.6.0`.
  - `[NEW] backend/services/__init__.py`
  - `[NEW] backend/services/email_service.py`
  - `[NEW] backend/templates/email_digest.html`
  - `[MODIFY] backend/main.py` — Add endpoints `GET /users/me/email-preferences`, `PUT /users/me/email-preferences`.
  - `[NEW] backend/tests/test_email_service.py`
- **Email Layout:** Responsive HTML with executive slate styling, Super Summary callout, 3 card modules, and call-to-actions ("Read Deep Dive", "Listen to Audio").
- **Verification:** `pytest backend/tests/test_email_service.py -v`.

---

### Checkpoint 21: Daily Audio Briefing Engine (Free Neural TTS)
- **Objective:** Automated 2–3 minute podcast-style MP3 briefing for commutes using 100% free Microsoft Neural TTS (`edge-tts`, zero API keys required, with optional OpenAI fallback).
- **Target Files:**
  - `[MODIFY] backend/requirements.txt` — Add `edge-tts==6.1.12`.
  - `[NEW] backend/services/audio_service.py`
  - `[MODIFY] backend/main.py` — Add `GET /briefing/today/audio`.
  - `[NEW] backend/tests/test_audio_service.py`
- **Implementation:**
  - Groq LLM writes a 300-word conversational radio broadcast script.
  - Call `edge_tts.Communicate(script, voice="en-US-ChristopherNeural")` to generate high-fidelity human-like speech for free.
  - Save MP3 to static/S3 storage and update `super_summaries.audio_url`.
- **Verification:** `pytest backend/tests/test_audio_service.py -v`.

---

### Checkpoint 22: Team Slack Bot & Workspace Integration
- **Objective:** Team workspace distribution via automated morning Slack Block Kit drops in `#market-intel`.
- **Target Files:**
  - `[MODIFY] backend/requirements.txt` — Add `slack-sdk==3.34.0`, `slack-bolt==1.22.0`.
  - `[NEW] backend/services/slack_service.py`
  - `[NEW] backend/routers/slack_router.py` — OAuth endpoints (`/slack/install`, `/slack/oauth_callback`).
  - `[MODIFY] backend/main.py` — Mount `slack_router`.
  - `[NEW] backend/tests/test_slack_service.py`
- **Implementation:** Formats Super Summary and top 3 cards into Slack Block Kit with interactive "Read Deep Dive" buttons. Posts via `WebClient(token=bot_token)`.
- **Verification:** `pytest backend/tests/test_slack_service.py -v`.

---

### Checkpoint 23: Frontend Modernization & Audio Player
- **Objective:** Update Expo mobile app with audio player widget, email settings, and 4-tier paywall with employer expensing receipt modal.
- **Target Files:**
  - `[MODIFY] frontend/package.json` — Add `expo-av@~15.0.2`.
  - `[NEW] frontend/src/components/AudioPlayer.tsx`
  - `[MODIFY] frontend/src/screens/HomeScreen.tsx` — Embed AudioPlayer above Super Summary.
  - `[MODIFY] frontend/src/screens/PaywallScreen.tsx` — 4-tier model (Free, Pro $9.99, Executive $24.99, Team $99).
  - `[NEW] frontend/src/components/ExpenseModal.tsx` — 1-click corporate reimbursement invoice.
  - `[MODIFY] frontend/src/types.ts` — Add `audio_url` and tier types.
- **Verification:** Frontend runs and AudioPlayer renders without crashes; Expense modal generates pre-formatted receipt.

---

### Checkpoint 24: Distributed Task Queue (Redis + Arq)
- **Objective:** Replace in-process scheduler with distributed Redis task queue.
- **Target Files:**
  - `[MODIFY] backend/requirements.txt` — Add `arq==0.26.1`, `redis==5.2.1`.
  - `[NEW] backend/worker.py` — Worker settings, registered tasks, cron schedules.
  - `[MODIFY] backend/main.py` — Connect to Redis.
  - `[NEW] docker-compose.yml` — Orchestrates FastAPI, Redis, and Arq worker.
  - `[NEW] backend/tests/test_worker_tasks.py`
- **Verification:** `pytest backend/tests/test_worker_tasks.py -v`.

---

### Checkpoint 25: Admin Dashboard 2.0 & Telemetry
- **Objective:** Operations dashboard displaying source health, daily LLM token costs, and multi-channel metrics.
- **Target Files:**
  - `[MODIFY] backend/admin.html` — Modern UI with Tailwind CSS and live telemetry.
  - `[MODIFY] backend/main.py` — Expand `GET /admin/stats` to report source health, API spend, and channel metrics.
  - `[NEW] backend/tests/test_admin_endpoints.py`
- **Verification:** `pytest backend/tests/test_admin_endpoints.py -v`.

---

## 3. Master Verification Matrix

| Checkpoint | Module | Primary Deliverable | Verification Command |
| :--- | :--- | :--- | :--- |
| **CP-16** | Ingestion | Modular HN, GitHub, arXiv, RSS scrapers | `pytest backend/tests/test_ingestion_sources.py` |
| **CP-17** | Database | PostgreSQL `pgvector`, `Team`, `SlackInstallation` tables | `pytest backend/tests/test_database_vector.py` |
| **CP-18** | Pipeline 1 | Global world-state clustering & pre-generation in `pipeline_stage1.py` | `pytest backend/tests/test_pipeline_stage1.py` |
| **CP-19** | Pipeline 2 | Stage 2 pgvector cosine matching in `pipeline_stage2.py` (<1.5s/user) | `pytest backend/tests/test_pipeline_stage2.py` |
| **CP-20** | Email | Resend API integration with responsive HTML digest | `pytest backend/tests/test_email_service.py` |
| **CP-21** | Audio | OpenAI TTS 2–3 min daily radio podcast generator | `pytest backend/tests/test_audio_service.py` |
| **CP-22** | Slack | Slack Bolt OAuth & Block Kit morning briefing in `#market-intel` | `pytest backend/tests/test_slack_service.py` |
| **CP-23** | Mobile UI | `AudioPlayer.tsx` on Home + 4-Tier Paywall & Employer Receipt Modal | `npm test (frontend)` |
| **CP-24** | Queue | Redis + `arq` worker pool & timezone-aware scheduler | `pytest backend/tests/test_worker_tasks.py` |
| **CP-25** | Admin | Admin Dashboard 2.0 with source health and API token spend tracker | `pytest backend/tests/test_admin_endpoints.py` |
