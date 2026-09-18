# NewsBrief Implementation Progress

## Checkpoint 1: Project Setup
- `[x]` Initialize FastAPI backend.
- `[x]` Initialize Expo / React Native frontend.
- `[x]` Setup basic project structure for both.
*Not implemented:* Database setup, external APIs, any specific UI screens.

## Checkpoint 2: Database Schema & Supabase Setup
- `[x]` Setup Supabase PostgreSQL connection in FastAPI.
- `[x]` Define SQLAlchemy/SQLModel schemas (`users`, `user_preferences`, `news_clusters`, `cards`, `super_summaries`, `deep_dives`, `user_briefings`, `daily_card_usage`).
- `[ ]` Run initial database migrations. *(Skipped until Supabase DB is active)*
*Not implemented:* Data insertion/fetching logic, Redis caching.

## Checkpoint 3: Google OAuth Authentication
- `[x]` Implement Google OAuth login logic in FastAPI.
- `[x]` Implement Google OAuth login in Expo app.
- `[x]` Protect backend routes with authentication middleware.
*Not implemented:* Native "Sign in with Apple" (deferred for MVP).

## Checkpoint 4: Onboarding API (Query Extraction)
- `[x]` Integrate Groq API (Qwen model) in the backend.
- `[x]` Implement `POST /onboarding/extract` endpoint to process free-text paragraphs into queries, tags, and tone.
- `[x]` Implement `POST /onboarding/confirm` endpoint to save user preferences.
*Not implemented:* Content moderation on the user's input paragraph.

## Checkpoint 5: Mobile Onboarding UI
- `[x]` Build text input screen for the interest paragraph.
- `[x]` Build preference confirmation screen (editable chips).
- `[x]` Connect the onboarding UI to the backend endpoints.
*Not implemented:* Post-onboarding preference editing (deferred for MVP).

## Checkpoint 6: Ingestion Pipeline (Google Search)
- `[x]` Implement `Serper` (Google Search) integration for news querying.
- `[x]` Implement `Jina Reader` API integration for URL text extraction.
- `[x]` Write script to iterate over active users, fetch their queries, and execute the ingestion pipeline.
*Not implemented:* Advanced proxy rotation, handling JS-heavy sites directly.

## Checkpoint 7: Embeddings & Clustering
- `[x]` Setup local `all-MiniLM-L6-v2` via `sentence-transformers`.
- `[x]` Implement basic semantic deduplication logic.
- `[x]` Write clustering step to group remaining articles by `thematic_tags` using Groq.
*Not implemented:* Postgres pgvector storage, cross-user cluster deduplication (handling per user for now).

## Checkpoint 8: Generation Pipeline (Cards & Super Summary)
- `[x]` Use Groq API to generate short Cards for each cluster and tone bucket.
- `[x]` Use Groq API to generate a daily Super Summary synthesizing all clusters.
- `[x]` Save generated content to `cards` and `super_summaries` tables.
- `[x]` Create `user_briefings` record linking the user to the day's content.

## Checkpoint 9: Deep Dive Generation
- `[x]` Use Groq API to generate structured Deep Dive research documents.
- `[x]` Implement endpoint `POST /content/deep-dive` for asynchronous generation.
- `[x]` Save generated content to `deep_dives` table.
*Not implemented:* Mobile reader UI for Deep Dives.

## Checkpoint 10: Mobile Home Screen
- `[x]` Implement `GET /briefing/today` endpoint.
- `[x]` Build Home screen UI rendering the daily Super Summary.
- `[x]` Handle empty/loading states gracefully.
*Not implemented:* Multi-timezone daily briefing logic.

## Checkpoint 11: Mobile Card Mode
- `[x]` Implement swipeable full-screen card stack using `react-native-reanimated`.
- `[x]` Enforce server-side rate limits on card viewing for free users.
*Not implemented:* Tapping to read Deep Dives on cards.

## Checkpoint 12: Mobile Deep Dive Reader & Read as One
- `[x]` Build Deep Dive streaming reader UI.
- `[x]` Implement "Read as One" consolidated view for premium users.
*Not implemented:* Personalized archive of past Deep Dives.

## Checkpoint 13: Subscription & Paywall (RevenueCat)
- `[x]` Integrate `react-native-purchases` for RevenueCat.
- `[x]` Build Paywall UI displaying premium benefits.
- `[x]` Connect frontend limit triggers (from CP-11) to Paywall.
*Not implemented:* Backend webhooks from RevenueCat to sync subscription status to DB.
*Not implemented:* Grace period logic for webhook delivery delays.

## Checkpoint 14: Batch Scheduler & Push Notifications
- `[x]` Configure `APScheduler` in FastAPI to run `run_pipeline.py` nightly.
- `[x]` Integrate Expo Push Notification SDK in backend.
- `[x]` Request notification permissions on frontend onboarding.
*Not implemented:* User-specific notification times.

## Checkpoint 15: Simple Admin Dashboard
- `[x]` Create basic internal endpoints for batch stats and manual triggers.
- `[x]` Build simple React admin page (or serve basic HTML from FastAPI).
*Not implemented:* Complex analytics, charting, or user moderation tooling.

---

# Redesign Phase: Autonomous Market & Competitor Intelligence (Checkpoints 16–25)

## Checkpoint 16: Multi-Source Ingestion Engine
- `[x]` Add `feedparser==6.0.11` and `httpx==0.27.0` to `backend/requirements.txt`.
- `[x]` Add `RawArticle` Pydantic model to `backend/schemas.py` (`id`, `title`, `url`, `source_name`, `content`, `published_at`, `tags`, `score`).
- `[x]` Implement `backend/ingestion_sources/hn.py` to query Hacker News Firebase API for top 30 stories with score >= 30.
- `[x]` Implement `backend/ingestion_sources/github.py` to query GitHub Search API for trending repos (>100 stars in last 7 days).
- `[x]` Implement `backend/ingestion_sources/arxiv.py` to query arXiv API for `cat:cs.AI OR cat:cs.LG OR cat:cs.CL` and parse XML abstracts.
- `[x]` Implement `backend/ingestion_sources/rss.py` to parse curated Substack/tech feeds using `feedparser`.
- `[x]` Write automated test `backend/tests/test_ingestion_sources.py` verifying >60 unique articles extracted.

## Checkpoint 17: Database Schema Migration & pgvector Integration
- `[x]` Add `pgvector==0.3.6` to `backend/requirements.txt`.
- `[x]` Register `pgvector` in `backend/db.py` (`CREATE EXTENSION IF NOT EXISTS vector`).
- `[x]` Add `embedding = Column(Vector(384))` to `models.NewsCluster` and `preference_embedding = Column(Vector(384))` to `models.UserPreference`.
- `[x]` Add B2B models to `backend/models.py`: `Team`, `TeamMembership`, `SlackInstallation`, and `UserEmailPreference`.
- `[x]` Add `audio_url` and `audio_duration_seconds` to `models.SuperSummary`.
- `[x]` Create and execute Alembic migration `backend/alembic/versions/0002_add_pgvector_and_b2b_models.py`.
- `[x]` Write automated test `backend/tests/test_database_vector.py` verifying vector insert and `<=>` cosine distance search.

## Checkpoint 18: Stage 1 Global World-State Pipeline
- `[x]` Implement `backend/pipeline_stage1.py` to run independently of individual users.
- `[x]` Concurrently aggregate articles across all 4 ingestion sources into a single raw pool (~400–600 items).
- `[x]` Deduplicate articles using `SentenceTransformer("all-MiniLM-L6-v2")` with cosine threshold 0.82.
- `[x]` Cluster surviving articles into 40–70 canonical clusters via Groq (`qwen/qwen3.8-27b`).
- `[x]` Calculate normalized centroid embedding for each cluster and assign to `NewsCluster.embedding`.
- `[x]` Pre-generate base Cards (`high_signal`, `technical_deep`) and top 10 Deep Dives once into the database.
- `[x]` Write automated test `backend/tests/test_pipeline_stage1.py` verifying DB persistence.

## Checkpoint 19: Stage 2 User Matching & Personalization Engine
- `[ ]` Implement `backend/pipeline_stage2.py` for personalized briefing generation.
- `[ ]` Auto-compute user preference vector if null (`raw_paragraph` + `thematic_tags` + `search_queries`).
- `[ ]` Query PostgreSQL for top 6 matching clusters via `ORDER BY embedding.cosine_distance(user_vector) LIMIT 6`.
- `[ ]` Synthesize custom Super Summary in user's specified `tone_bucket` via Groq.
- `[ ]` Create and link `UserBriefing` record (execution speed < 1.5s per user).
- `[ ]` Add endpoint `POST /admin/trigger-stage2` in `backend/main.py`.
- `[ ]` Write automated test `backend/tests/test_pipeline_stage2.py`.

## Checkpoint 20: Daily Email Digest Service (Resend Integration)
- `[ ]` Add `resend==2.6.0` to `backend/requirements.txt`.
- `[ ]` Implement `backend/services/email_service.py` to dispatch HTML emails via Resend API.
- `[ ]` Design responsive HTML template `backend/templates/email_digest.html` with Super Summary, top 3 cards, and deep dive links.
- `[ ]` Add endpoints `GET /users/me/email-preferences` and `PUT /users/me/email-preferences` in `backend/main.py`.
- `[ ]` Write automated test `backend/tests/test_email_service.py` with mocked Resend client.

## Checkpoint 21: Daily Audio Briefing Engine (TTS)
- `[ ]` Add `openai==1.65.0` to `backend/requirements.txt`.
- `[ ]` Implement `backend/services/audio_service.py`: prompt Groq for 300-word broadcast script and synthesize via OpenAI TTS (`tts-1`, voice `onyx`).
- `[ ]` Store MP3 in `backend/static/audio/{batch_date}/{summary_id}.mp3` and set `SuperSummary.audio_url`.
- `[ ]` Expose streaming endpoint `GET /briefing/today/audio` in `backend/main.py`.
- `[ ]` Write automated test `backend/tests/test_audio_service.py` verifying valid MP3 output.

## Checkpoint 22: Team Slack Bot & Workspace Integration
- `[ ]` Add `slack-sdk==3.34.0` and `slack-bolt==1.22.0` to `backend/requirements.txt`.
- `[ ]` Implement `backend/services/slack_service.py` to construct Block Kit payloads for briefings.
- `[ ]` Implement `backend/routers/slack_router.py` with OAuth routes (`/slack/install`, `/slack/oauth_callback`).
- `[ ]` Mount Slack router in `backend/main.py`.
- `[ ]` Write automated test `backend/tests/test_slack_service.py` verifying Block Kit schema.

## Checkpoint 23: Frontend Modernization & Audio Player
- `[ ]` Add `expo-av@~15.0.2` to `frontend/package.json`.
- `[ ]` Create `frontend/src/components/AudioPlayer.tsx` with Play/Pause and progress bar.
- `[ ]` Embed `AudioPlayer` on `HomeScreen.tsx` above Super Summary.
- `[ ]` Update `PaywallScreen.tsx` with 4-tier pricing ($0 Free, $9.99 Pro, $24.99 Executive, $99 Team).
- `[ ]` Create `frontend/src/components/ExpenseModal.tsx` for 1-click corporate reimbursement receipts.
- `[ ]` Update `frontend/src/types.ts` with `audio_url` and new subscription tier types.

## Checkpoint 24: Distributed Task Queue (Redis + Arq)
- `[ ]` Add `arq==0.26.1` and `redis==5.2.1` to `backend/requirements.txt`.
- `[ ]` Implement `backend/worker.py` configuring Arq worker, cron schedules (03:00 UTC Stage 1, hourly Stage 2), and retry policies.
- `[ ]` Create `docker-compose.yml` orchestrating FastAPI, Redis, and Arq worker.
- `[ ]` Write automated test `backend/tests/test_worker_tasks.py`.

## Checkpoint 25: Admin Dashboard 2.0 & Telemetry
- `[ ]` Revamp `backend/admin.html` with Tailwind CSS, source health indicators (HN, GitHub, arXiv, RSS), and cost counters.
- `[ ]` Expand `GET /admin/stats` in `backend/main.py` to return source counts, token spend, and channel metrics.
- `[ ]` Add manual trigger buttons for Stage 1, Stage 2, and test email.
- `[ ]` Write automated test `backend/tests/test_admin_endpoints.py`.


