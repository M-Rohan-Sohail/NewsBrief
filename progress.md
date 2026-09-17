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
