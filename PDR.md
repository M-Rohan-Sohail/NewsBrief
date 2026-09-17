# NewsBrief — Technical Specification (PDR v2)

**Document type:** Implementation-ready technical specification
**Supersedes:** PDR v1 (architecture/workflow/design-rules overview)
**Audience:** Coding agent / engineering team
**Convention used throughout:** Any requirement not explicitly discussed and confirmed in product planning is marked **`[OPEN DECISION]`** or **`[ASSUMPTION]`** inline, and re-listed in Section 20. Nothing marked this way should be treated as final — it is a proposed default so the spec stays implementable, not a decision.

---

## Table of Contents
1. [Product Vision & Problem Statement](#1-product-vision--problem-statement)
2. [Target Users & Personas](#2-target-users--personas)
3. [Core Features & Functionality](#3-core-features--functionality)
4. [Complete User Flows](#4-complete-user-flows)
5. [System Architecture & Major Components](#5-system-architecture--major-components)
6. [Frontend/UI Requirements](#6-frontendui-requirements)
7. [Backend Architecture & APIs](#7-backend-architecture--apis)
8. [Database Schema & Relationships](#8-database-schema--relationships)
9. [AI/ML Components](#9-aiml-components)
10. [Authentication, Authorization & Security](#10-authentication-authorization--security)
11. [Integrations & External Services](#11-integrations--external-services)
12. [Functional Requirements](#12-functional-requirements)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Edge Cases & Error Handling](#14-edge-cases--error-handling)
15. [Admin/Dashboard Requirements](#15-admindashboard-requirements)
16. [Technology Stack & Constraints](#16-technology-stack--constraints)
17. [Feature Priorities (MVP vs Future)](#17-feature-priorities-mvp-vs-future)
18. [Acceptance Criteria](#18-acceptance-criteria)
19. [Deployment & Infrastructure](#19-deployment--infrastructure)
20. [Assumptions & Open Decisions (Consolidated)](#20-assumptions--open-decisions-consolidated)

---

## 1. Product Vision & Problem Statement

**Problem:** Users tracking a fast-moving niche via social feeds (X, LinkedIn) encounter high duplicate-content rates (multiple reposts of the same event), no natural stopping point (infinite scroll), and no depth control (every item is either a headline or a full article, nothing in between).

**Solution:** One daily batch-generated briefing per user, built from a single onboarding description of their interests, delivered at three fixed depths:
- **Card** — 3-4 bullets, one story, one source link.
- **Super Summary** — synthesis of the day's top 5-6 stories into one narrative.
- **Deep Dive** — 400-700 word structured research document, generated per story on explicit request.

**Explicit non-goals:**
- Not a social network (no comments, follows, sharing graph).
- Not a real-time alert system — one batch per day, not continuous push.
- Not a general news reader — content is scoped strictly to what a user's stated interests match.

---

## 2. Target Users & Personas

`[ASSUMPTION]` These personas are constructed from the stated target audience ("busy professionals, developers, founders") for the purpose of grounding UI/tone decisions. They are not based on user research or interviews — validate against real users post-launch before treating them as fact.

| | Persona A — "Builder" | Persona B — "Operator" |
|---|---|---|
| Role | Founder or senior engineer in a specific technical niche (e.g. AI infra, open-source LLMs) | Product manager or generalist professional monitoring a domain for decision-making, not implementation |
| Reading window | Short, fragmented (commute, first coffee) | Similar, but more likely to return mid-day for a Deep Dive before a meeting |
| Tolerance for fluff | Very low — will churn on hype-y phrasing | Moderate — cares more about "what changed" than technical precision |
| Likely tone_bucket | `high_signal` or `technical_deep` | `casual` or `executive_brief` |
| Primary value driver | Time saved vs. manually filtering feeds | Staying credibly informed without becoming a full-time reader |
| Deep Dive usage pattern | Frequent, on stories in their exact niche | Occasional, on the 1-2 biggest stories of the day |

Both personas are the basis for tone-bucket coverage (Section 9) — the 5 fixed buckets must include at least one that fits each persona well; this is why `high_signal`/`technical_deep` and `casual`/`executive_brief` both exist as separate buckets rather than collapsing to one.

---

## 3. Core Features & Functionality

| Feature | Description | Tier |
|---|---|---|
| Natural-language onboarding | Free-text paragraph → extracted queries/tags/tone | Free + Premium |
| Preference confirmation | Editable chip UI before persisting extracted preferences | Free + Premium |
| Preference editing (post-onboarding) | `[ASSUMPTION]` Re-run extraction or manually edit chips after initial onboarding; exact flow not discussed — assumed necessary since a one-shot, never-editable onboarding is not a viable product | Free + Premium |
| Super Summary | Daily synthesis of top 5-6 stories | Free + Premium (unlimited) |
| Quick Cards | Swipeable single-story cards | Free (capped 5/day), Premium (unlimited) |
| Deep Dive (per card) | On-demand or pre-generated research doc per story | Premium only |
| Read as one | Concatenated view of pre-generated top-story Deep Dives | Premium only |
| Personalized archive | `[OPEN DECISION]` Original product spec named this as a premium feature ("full personalized archives"); no retention window, UI, or query pattern has been designed. Data model supports it via `user_briefings` history, but scope is undefined. | Premium (scope open) |
| Push notifications | Daily notification naming the top Deep Dive story | Free + Premium |
| Subscription purchase | RevenueCat-mediated IAP | — |
| Admin operations | `[OPEN DECISION]` Not discussed prior to this document; minimal proposed scope in Section 15 | Internal |

---

## 4. Complete User Flows

### 4.1 Onboarding & Preference Confirmation
1. User opens app for the first time → onboarding screen (no account gating before this step, see Section 10).
2. User submits a free-text paragraph.
3. **Validation (client + server):** reject if paragraph length < 20 characters `[ASSUMPTION: exact threshold]`. Do not call the LLM on an empty/trivial input.
4. Backend calls query extraction (Section 9.1) → returns unsaved `{search_queries, thematic_tags, tone_bucket, tone_freeform, exclude_keywords}`.
5. App renders result as editable chips grouped by type (queries / tags / tone).
6. User edits, removes, or adds chips; tone_bucket is chosen from a fixed 5-option selector, not free text.
7. User confirms → `POST /onboarding/confirm` persists to `user_preferences`.
8. App proceeds to account creation/login if not already authenticated `[OPEN DECISION — see Section 10 on whether auth precedes or follows onboarding]`.

**Failure branch:** if extraction fails or returns malformed data after retry (Section 9.1), show an inline error and allow resubmission — never silently proceed with empty/default preferences.

### 4.2 Daily Briefing Consumption
1. Push notification arrives (single fixed timezone, Section 13) naming the top Deep Dive story.
2. Tap → deep-links to Home, which loads `GET /briefing/{user_id}/today`.
3. Home renders the Super Summary first (zero additional taps).
4. User proceeds to Card Mode (explicit navigation, not automatic) → full-screen swipeable stack.
5. On each card, user may: swipe to next card, or tap Deep Dive.
6. **Free user taps Deep Dive:** blocked, paywall shown (Section 6).
7. **Free user reaches their 6th card of the day:** blocked, paywall shown; server enforces this independent of client state (Section 14).
8. User exhausts all matched cards for the day → "you're caught up" end screen, not an empty/blank state.

### 4.3 Deep Dive (On-Demand)
1. Premium user taps Deep Dive on a card.
2. `POST /deep-dive/{cluster_id}`.
3. **Cache hit** (pre-generated or previously requested by any user): returned immediately.
4. **Cache miss:** backend calls Claude (Section 9.4), response streamed to client as it generates; result persisted and becomes a cache hit for every subsequent user.
5. **Generation failure:** client shows a retry affordance; no partial/empty result is cached (Section 14).

### 4.4 Read as One
1. Premium user toggles "Read as one" on Home.
2. Client requests the pre-generated Deep Dives for the day's top-cluster set (already fetched as part of the day's briefing, or a dedicated read endpoint — `[OPEN DECISION: whether this is a new endpoint or reuses existing Deep Dive records already client-side]`).
3. Renders Super Summary as the intro paragraph, followed by each top story's Deep Dive in sequence.
4. **Never** triggers on-demand generation for a cluster missing from this set (R-UX1, unchanged from v1).

### 4.5 Subscription Purchase
1. User taps upgrade (from paywall or a dedicated settings entry point).
2. RevenueCat SDK presents the native Apple/Google purchase sheet.
3. On success, RevenueCat validates the receipt and fires a webhook to the backend.
4. Backend updates `users.subscription_status`; gates unlock on the user's next request (no client-side optimistic unlock without server confirmation — see Section 14 for the race condition this implies).

---

## 5. System Architecture & Major Components

```
Mobile App (Expo/RN) ──HTTPS/JSON──▶ FastAPI Backend ──▶ Postgres (system of record)
      │                                    │      │
      │◀── Expo Push ── Scheduler ─────────┘      └──▶ Redis (cluster×tone-bucket cache)
      │
      └── RevenueCat SDK ──▶ RevenueCat ──webhook──▶ FastAPI Backend

FastAPI Backend, on batch trigger, calls:
  → Serper News API        (ingestion)
  → local embedding model  (in-process, dedup/clustering)
  → Claude API              (card / super summary / deep dive generation)
```

| Component | Responsibility |
|---|---|
| Mobile App | All UI/UX (Section 6), RevenueCat SDK integration, push token registration, streamed Deep Dive rendering |
| FastAPI Backend | All endpoints (Section 7), orchestrates the pipeline, owns all gating/authorization decisions |
| Scheduler | Triggers the morning batch once per day, single fixed timezone (Section 13) |
| Postgres | System of record — all tables in Section 8 |
| Redis | Fast-path cache during a batch run for `(cluster_id, tone_bucket)` lookups; Postgres is the durable copy, Redis is not authoritative |
| Serper News API | External ingestion, 24h window, queried once per unique query in the shared pool |
| Local embedding model | `all-MiniLM-L6-v2`, in-process, no external API call |
| Claude API | All generation calls, model-tiered (Section 9) |
| RevenueCat | Wraps Apple/Google IAP, source of truth for subscription state |

---

## 6. Frontend/UI Requirements

Convention: each screen lists Purpose, Data source, States, and Key interactions. Loading/error/empty states are mandatory for every screen that fetches data — a screen with only a "success" state is not spec-complete.

### 6.1 Onboarding
- **Purpose:** capture the interest paragraph.
- **Data source:** none in (write-only until submit).
- **States:** empty input (submit disabled), submitting (loading indicator on the extraction call), error (extraction failed — show inline retry).
- **Interactions:** single multiline text field, submit button.

### 6.2 Preference Confirmation
- **Purpose:** show extracted preferences for correction before persisting.
- **Data source:** response of `/onboarding/extract`.
- **States:** loaded (chips editable), saving (on confirm tap), error (confirm failed — retain edits, allow retry, do not lose user's edits on failure).
- **Interactions:** remove/add query and tag chips; tone selected from a fixed 5-option control (not free text, to prevent drift from the bucket system); confirm button persists via `/onboarding/confirm`.

### 6.3 Home / Today
- **Purpose:** daily habit hook — Super Summary first.
- **Data source:** `GET /briefing/{user_id}/today`.
- **States:**
  - Loading: skeleton, not blank screen.
  - Success: Super Summary rendered, entry point into Card Mode below it.
  - **Empty (no matched clusters today):** explicit message that no stories matched the user's interests today, with a prompt to broaden preferences — **not** a blank or broken-looking screen. `[ASSUMPTION: exact copy/design not specified]`
  - Error (briefing not yet generated / fetch failed): distinct from the empty-match state — this means the batch hasn't run or failed, not that there's genuinely nothing to show.
- **Interactions:** navigate to Card Mode; "Read as one" toggle (premium only, hidden/disabled with an upsell affordance for free users).

### 6.4 Card Mode
- **Purpose:** primary consumption surface.
- **Data source:** `cards` array from the same briefing response.
- **States:** in-progress (stack with N cards remaining), free-tier-limit-reached (paywall, Section 6.7), end-of-stack ("you're caught up").
- **Interactions:** swipe to advance (`react-native-reanimated`), tap Deep Dive per card, next card peeks at the bottom edge.
- **Server-enforced constraint:** the 6th card request from a free user must be rejected server-side (Section 14) — the client must handle this as an explicit paywall trigger, not assume its own local counter is authoritative.

### 6.5 Deep Dive Reader
- **Purpose:** Tier-3 content display.
- **Data source:** `POST /deep-dive/{cluster_id}` response, streamed.
- **States:** streaming (tokens appear progressively, not a blocking spinner), complete, error (retry affordance, distinct from a slow-but-working stream).
- **Interactions:** scroll to read; no editing.

### 6.6 Read as One
- **Purpose:** single-document view of the day's top stories.
- **Data source:** already-fetched Deep Dive content for the day's top-cluster set only.
- **States:** available (premium, top clusters have Deep Dives), unavailable (should not occur if batch pre-generation succeeded — treat as an error state and log if it does, per R10/Section 14).
- **Constraint:** must never issue a network call to the on-demand Deep Dive endpoint for a cluster outside the pre-generated top set.

### 6.7 Paywall
- **Purpose:** convert free users at the moment of highest intent.
- **Trigger conditions only:** free-tier card cap reached, or any Deep Dive tap by a free user. **Never shown unprompted on first open.**
- **States:** default (plan options + price), purchasing (RevenueCat sheet in progress), success (dismiss, unlock immediately), failure (return to prior screen, no state change).

### 6.8 Preference Editing
`[ASSUMPTION]` Not designed in product planning. Proposed minimal scope: a settings entry point that re-opens the Preference Confirmation screen (6.2) pre-filled with current values, allowing the same add/remove/tone-change interactions, submitting to a (currently undefined) update endpoint — see Section 7 gap.

---

## 7. Backend Architecture & APIs

### 7.1 Modules
`main.py` (routes) · `models.py` (schemas) · `prompts.py` (LLM prompts) · `pipeline.py` (extraction/ingestion/generation logic) · `embeddings_dedup.py` (clustering) · `scheduler.py` (batch trigger) · `webhooks.py` (RevenueCat receiver) · `auth.py` `[OPEN DECISION — depends on Section 10]` · `db.py`

### 7.2 Endpoints

| Method | Path | Purpose | Auth | Notes |
|---|---|---|---|---|
| `POST` | `/onboarding/extract` | Run query extraction, return unsaved result | User `[or anonymous pre-auth, OPEN]` | Rate-limited per Section 10 (LLM-cost-bearing) |
| `POST` | `/onboarding/confirm` | Persist confirmed preferences | User | |
| `PUT` | `/preferences` | `[OPEN DECISION]` Update existing preferences | User | Not designed; needed for 4.1/6.8 |
| `GET` | `/briefing/{user_id}/today` | Return today's briefing, gated by free-tier cap | User (must match `user_id`, see 10.2) | No synchronous generation on this path (R-perf) |
| `POST` | `/deep-dive/{cluster_id}` | Return cached or generate on-demand Deep Dive | User, premium-gated server-side | Rate-limited per Section 10 |
| `GET` | `/archive` | `[OPEN DECISION]` Historical briefings | User, premium-gated | Scope undefined, see Section 3 |
| `POST` | `/push-token` | Register/update Expo push token | User | Overwrites prior token (single device, `[ASSUMPTION]`) |
| `POST` | `/webhooks/revenuecat` | Receive subscription state changes | Webhook signature | Must be idempotent (Section 14) |
| `POST` | `/internal/run-batch` | Manually trigger the batch | Internal/admin | Not exposed to regular users |

### 7.3 Example Response Shape — `GET /briefing/{user_id}/today`
```json
{
  "user_id": "uuid",
  "briefing_date": "2026-09-16",
  "super_summary": {
    "headline": "string",
    "synthesis": "string",
    "contributing_cluster_ids": ["uuid"]
  },
  "cards": [
    {
      "cluster_id": "uuid",
      "headline": "string",
      "bullets": ["string", "string", "string"],
      "source_name": "string",
      "source_url": "string",
      "tags": ["string"],
      "has_deep_dive_ready": true
    }
  ],
  "cards_remaining_today": 3
}
```
**Empty-match case:** `cards: []`, `super_summary: null` — client renders the empty state from Section 6.3, not an error.

---

## 8. Database Schema & Relationships

```sql
users
  id                    UUID PK
  email                 TEXT NULL          -- [OPEN DECISION: auth mechanism, Section 10]
  created_at            TIMESTAMPTZ NOT NULL
  timezone              TEXT NOT NULL       -- fixed system value for MVP, not user-set
  subscription_status   TEXT NOT NULL       -- 'free' | 'premium' | 'grace_period' | 'cancelled'
  revenuecat_user_id    TEXT NULL
  expo_push_token       TEXT NULL           -- single device, [ASSUMPTION]

user_preferences
  user_id               UUID PK, FK -> users.id      -- one active row per user (MVP: no history)
  raw_paragraph         TEXT NOT NULL
  search_queries        TEXT[] NOT NULL
  thematic_tags         TEXT[] NOT NULL
  tone_bucket           TEXT NOT NULL         -- enum: high_signal|casual|beginner_friendly|technical_deep|executive_brief
  tone_freeform         TEXT NULL
  exclude_keywords      TEXT[] NULL
  updated_at            TIMESTAMPTZ NOT NULL

news_clusters
  id                    UUID PK
  batch_date            DATE NOT NULL
  canonical_title       TEXT NOT NULL
  representative_snippet TEXT NOT NULL
  source_count          INT NOT NULL
  matched_tags          TEXT[] NOT NULL
  article_refs          JSONB NOT NULL        -- [{title, snippet, source, link}]
  INDEX (batch_date)

cards
  id                    UUID PK
  cluster_id            UUID FK -> news_clusters.id
  tone_bucket           TEXT NOT NULL
  headline              TEXT NOT NULL
  bullets               TEXT[] NOT NULL
  source_name           TEXT NOT NULL
  source_url            TEXT NOT NULL
  generated_at          TIMESTAMPTZ NOT NULL
  UNIQUE (cluster_id, tone_bucket)

super_summaries
  id                        UUID PK
  batch_date                DATE NOT NULL
  cluster_set_key           TEXT NOT NULL      -- hash of sorted contributing cluster_ids
  tone_bucket               TEXT NOT NULL
  headline                  TEXT NOT NULL
  synthesis                 TEXT NOT NULL
  contributing_cluster_ids  UUID[] NOT NULL     -- array for MVP simplicity; revisit as join table post-MVP if needed
  UNIQUE (cluster_set_key, tone_bucket)

deep_dives
  id                    UUID PK
  cluster_id            UUID FK -> news_clusters.id, UNIQUE   -- one per cluster, tone_freeform not cache-keyed (R5)
  title                 TEXT NOT NULL
  body_markdown         TEXT NOT NULL
  pre_generated         BOOLEAN NOT NULL
  generated_at          TIMESTAMPTZ NOT NULL

user_briefings
  user_id               UUID FK -> users.id
  batch_date            DATE NOT NULL
  super_summary_id      UUID FK -> super_summaries.id NULL   -- null on empty-match days
  card_ids              UUID[] NOT NULL                       -- array for MVP simplicity, see above
  PRIMARY KEY (user_id, batch_date)

daily_card_usage
  user_id               UUID FK -> users.id
  date                  DATE NOT NULL
  cards_viewed_count     INT NOT NULL DEFAULT 0
  PRIMARY KEY (user_id, date)
```

**Relationships:**
- `users` 1—1 `user_preferences` (MVP: single active profile; no preference history/versioning).
- `news_clusters` 1—N `cards` (up to 5, one per tone bucket actually in use that day).
- `news_clusters` 1—1 `deep_dives`.
- `users` 1—N `user_briefings` (one per calendar date), 1—N `daily_card_usage` (one per calendar date).
- Array-column relationships (`contributing_cluster_ids`, `card_ids`) are an explicit MVP simplification, not an oversight — flagged for revisit if query patterns need proper joins post-MVP.

---

## 9. AI/ML Components

| # | Component | Model tier | Input | Output (schema) | Failure handling |
|---|---|---|---|---|---|
| 9.1 | Query extraction | Strong (low volume) | `raw_paragraph: string` | `{search_queries[5-8], thematic_tags[4-8], tone_bucket: enum(5), tone_freeform, exclude_keywords[]}`, strict JSON | Invalid JSON or invalid `tone_bucket` value → retry once with the same input. Still invalid → fail the request with an error to the client; never persist a partial/guessed result. |
| 9.2 | Embedding + clustering | Local model, no API | `[{title, snippet}]` per article | List of clusters (greedy single-pass, cosine similarity ≥ 0.82, configurable) | Model load/inference failure → **fail the batch run loudly** (alert), do not silently skip dedup — skipping would multiply downstream LLM cost by however many duplicate articles exist per event. |
| 9.3 | Card generation | Cheap/fast (high volume) | `{cluster: {canonical_title, articles[]}, tone_bucket → resolved description}` | `{headline, bullets[3-4], source_name, source_url}`, strict JSON | Invalid JSON → retry once → still invalid: **skip this card for this batch** (log cluster_id + tone_bucket), do not fail the whole batch. |
| 9.4 | Super Summary | Strong (low volume) | `{top_clusters[5-6], tone}` | `{headline, synthesis (150-250 words), contributing_cluster_ids}` | Same retry-then-skip. If skipped, the affected users' briefing has cards but `super_summary: null` — graceful degradation, not a blocked briefing. |
| 9.5 | Deep Dive | Strong (per-cluster, cached) | `{cluster full article set, tone_freeform}` | Structured Markdown, 400-700 words | On-demand: client-visible error + retry affordance, no partial result cached. Pre-gen (batch): retry once, then leave absent — client shows "Deep dive unavailable" for that story rather than blocking the rest of the briefing. |

**Grounding constraint (applies to 9.1, 9.3, 9.4, 9.5):** every generation prompt must instruct the model to use only provided source material and omit rather than fabricate when material is insufficient. No output may reproduce more than one verbatim quote under 15 words from any single source article.

---

## 10. Authentication, Authorization & Security

**`[OPEN DECISION]` — authentication mechanism is undecided.** This was never specified in product planning. Requirements below are split into what's true regardless of mechanism, and a proposed default.

### 10.1 Mechanism-independent requirements
- Every endpoint except `/webhooks/revenuecat` requires a verified user identity.
- Authorization model is row-level ownership only — a user may only read/write their own `user_preferences`, `user_briefings`, `daily_card_usage`. There is no team/shared-account concept in MVP.
- No endpoint may accept a client-supplied `user_id` for a different user's data without server-side identity verification matching it.

### 10.2 Proposed default `[OPEN DECISION — confirm before build]`
- Email-based passwordless (magic link) or "Sign in with Apple" / "Sign in with Google."
- **Platform constraint (not open — this is an Apple policy, not a product choice):** if any third-party social login (e.g. Google) is offered, Apple requires "Sign in with Apple" to also be offered as an equivalent option for App Store approval.
- Session strategy: short-lived JWT access token + refresh token, standard pattern. `[ASSUMPTION]`

### 10.3 Security requirements (not open — apply regardless of auth mechanism)
- Secrets (`ANTHROPIC_API_KEY`, `SERPER_API_KEY`, `REVENUECAT_WEBHOOK_SECRET`, DB credentials) via environment variables only — never logged, never hardcoded.
- `/webhooks/revenuecat` must verify the signature header before trusting payload contents.
- **Rate limiting required** on `/onboarding/extract` and `/deep-dive/{cluster_id}` — both trigger LLM calls; without a per-user limit, a buggy or malicious client can generate unbounded cost. Exact limits `[ASSUMPTION — propose e.g. 5 extraction calls/hour, 20 deep-dive requests/hour per user]`.
- Free-tier and premium-tier gates (card cap, Deep Dive access) must be enforced server-side on every request — never trust a client-reported count or entitlement state (Section 14).

### 10.4 Data privacy `[OPEN DECISION]`
GDPR/CCPA compliance posture has not been reviewed. The onboarding paragraph and derived preferences are personal data (interest profiling); flagged for legal review before public launch, same as the copyright posture in Section 9's grounding constraint.

---

## 11. Integrations & External Services

| Service | Purpose | Data exchanged | Failure/outage handling |
|---|---|---|---|
| Serper News API | Ingestion, 24h window | Queries out; articles in | Per-query timeout/failure → skip that query, continue the pool (partial success, not batch failure) |
| Claude API (Anthropic) | All generation (9.1-9.5) | Prompts out; JSON/Markdown in | Retry-then-skip pattern per component (Section 9) |
| RevenueCat | Subscription/entitlement source of truth | Webhook events in | `[PROPOSED, not confirmed]` Add a periodic reconciliation job polling RevenueCat's API as a safety net against missed webhook deliveries — webhook-only sync can drift silently |
| Expo Push Service | Notification delivery | Push tokens out; delivery receipts in | An invalid/expired-token delivery receipt must prune `users.expo_push_token`, not retry indefinitely |
| `sentence-transformers` (local) | Embeddings for dedup | None (local inference) | See Section 9.2 |

---

## 12. Functional Requirements

| ID | Requirement |
|---|---|
| FR-ONB-1 | System shall reject onboarding paragraphs below a minimum length without calling the LLM. |
| FR-ONB-2 | System shall not persist extracted preferences until the user explicitly confirms them. |
| FR-ONB-3 | `tone_bucket` shall always be constrained to the 5 fixed values; the client shall never accept free-text tone input. |
| FR-GEN-1 | The system shall generate at most one Card per `(cluster_id, tone_bucket)` pair per `batch_date`. |
| FR-GEN-2 | The system shall generate at most one Super Summary per `(cluster_set_key, tone_bucket)` pair per `batch_date`. |
| FR-GEN-3 | The system shall generate at most one Deep Dive per `cluster_id`, regardless of how many users or tone preferences request it. |
| FR-DD-1 | The system shall pre-generate Deep Dives during the batch run for every cluster that appears in any user's top-6 matched set. |
| FR-DD-2 | On-demand Deep Dive generation shall only occur on a cache miss. |
| FR-GATE-1 | Free-tier users shall be limited to 5 card views per calendar day, enforced server-side. |
| FR-GATE-2 | Free-tier users shall have zero access to Deep Dive generation or retrieval, enforced server-side. |
| FR-BILL-1 | Subscription state changes shall be reflected in gating decisions immediately upon webhook receipt, without requiring the user to restart the app. |
| FR-NOTIF-1 | The daily notification shall reference the top pre-generated Deep Dive story by name. |
| FR-ARCHIVE-1 | `[OPEN DECISION]` Undefined pending Section 3/7 archive scope decision. |

---

## 13. Non-Functional Requirements

| Category | Requirement | Status |
|---|---|---|
| Performance | `GET /briefing/today` must be servable from pre-generated rows only — zero synchronous generation on this path | Confirmed (follows directly from architecture) |
| Performance | Target response time for `GET /briefing/today`: sub-second (DB read only) | `[ASSUMPTION — proposed target, not validated against real infra]` |
| Scalability | LLM call volume must scale with distinct cluster/tone-bucket/cluster-set combinations, not with user count | Confirmed (core architectural principle) |
| Scalability | Single backend instance is acceptable at MVP scale; horizontal scaling is deferred | Confirmed for MVP |
| Availability | No formal uptime SLA | `[OPEN DECISION]` |
| Cost | Cache-hit rate (LLM calls made vs. calls that would be needed per-user) is the primary architectural health metric | Confirmed |
| Idempotency | The batch job must be safely re-runnable for a given `batch_date` without duplicating clusters/cards/summaries/deep-dives | Confirmed (R10) |
| Localization | English only for MVP | Confirmed |

---

## 14. Edge Cases & Error Handling

| Scenario | Expected behavior |
|---|---|
| Onboarding paragraph empty/too short | Reject client + server side before any LLM call (FR-ONB-1) |
| Extraction returns invalid JSON | Retry once, then fail the request with a client-visible error (Section 9.1) |
| Extraction returns an out-of-enum `tone_bucket` | Retry once; if still invalid, fall back to a default bucket (`[ASSUMPTION: default = high_signal]`) rather than failing onboarding entirely |
| A Serper query returns zero results | Skip that query, continue the shared pool |
| All queries in the pool return zero results | Batch completes with zero clusters; affected users see the empty-match Home state (6.3), not an error |
| A user has zero matched clusters on a given day | Explicit empty state, not blank/broken UI (6.3) |
| Clustering produces one abnormally large cluster (threshold too loose) | No automatic runtime correction in MVP; log cluster-size distribution per batch for manual threshold tuning |
| Card/Summary/Deep-Dive generation fails for one item | Skip that item, log it, continue the batch — partial batch success is required, a single generation failure must never fail the entire run |
| Deep Dive on-demand generation times out | Client shows retry, not an infinite spinner; no partial result is cached |
| Free user attempts to access Deep Dive via a direct API call (bypassing UI) | Server rejects independent of client state — gating is never client-only enforced |
| Free user's 6th card request | Server rejects with a paywall-trigger response, independent of any client-side counter |
| RevenueCat webhook delivered twice for the same event | Handler must be idempotent (dedupe on event ID) |
| RevenueCat webhook indicates cancellation/downgrade | Premium gates revoked on the user's next request — no grace period unless RevenueCat's own payload indicates one |
| Purchase succeeds client-side but webhook is delayed | `[OPEN DECISION]` Client should not optimistically unlock premium before server confirmation, which means a brief lag between payment and access is possible — acceptable for MVP or needs a client-side "pending" state, not yet decided |
| Push token becomes invalid (delivery receipt error) | Prune the token from `users.expo_push_token`; do not keep retrying |
| Batch job crashes mid-run | Must be safely re-runnable for the same `batch_date` without duplicating already-completed work (R10) |
| User outside the single supported timezone (MVP) | Notification still fires at the fixed batch timezone regardless of the user's actual location — documented limitation, not a bug, until Section 17's post-MVP multi-timezone work |
| Onboarding paragraph contains abusive/policy-violating content | `[OPEN DECISION]` No content moderation policy defined for user-submitted paragraphs |

---

## 15. Admin/Dashboard Requirements

`[OPEN DECISION]` Not discussed in prior product planning. The following is a proposed minimal scope required to operate the product — not a confirmed requirement set.

**Proposed MVP-necessary (P1):**
- Batch run history: status, cluster count, LLM call count, cache-hit rate per run — this is the direct evidence that the shared-pool architecture is functioning (Section 13).
- Manual batch trigger (already specified as `/internal/run-batch`).
- User lookup by ID/email: preferences, subscription status, recent briefing history — for support purposes.
- Aggregate daily cost/usage: LLM calls by type, Serper calls.

**Explicitly proposed out of scope for MVP:**
- Content moderation tooling.
- Full analytics/charting dashboards.
- User ban/delete tooling.
- Refund/billing management — RevenueCat's own dashboard already covers this; no need to rebuild it.

**Access control:** `[OPEN DECISION]` Admin surface must not be reachable by regular authenticated users. Exact mechanism (separate internal auth, IP allowlist, etc.) undecided.

---

## 16. Technology Stack & Constraints

| Layer | Choice | Constraint |
|---|---|---|
| Backend | Python / FastAPI | — |
| Database | PostgreSQL | `[ASSUMPTION — not explicitly confirmed, but implied by architecture]` |
| Cache | Redis | `[ASSUMPTION]` |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`), local | Must load once per process, not per request (cold-start cost) |
| LLM | Claude API, model-tiered | Cheap/fast model for Cards, strong model for Extraction/Summary/Deep Dive (Section 9) |
| Mobile | Expo (React Native) | Single codebase, OTA JS updates via EAS |
| Swipe/animation | `react-native-reanimated` | — |
| Push | Expo Push Service (APNs/FCM) | Native push required — PWA push is unreliable on iOS, ruling out a web-only MVP |
| Billing | RevenueCat | Apple/Google require native IAP for digital subscriptions consumed in-app; Stripe cannot be used directly for this |
| Scheduler | APScheduler (in-process) | **Only viable on a single, always-on instance.** If infrastructure is serverless or multi-instance, this must be replaced with an external cron hitting `/internal/run-batch`, or the batch will run duplicately per instance |

---

## 17. Feature Priorities (MVP vs Future)

| Feature | Priority | Notes |
|---|---|---|
| Onboarding + confirmation | P0 | |
| Card generation + delivery | P0 | |
| Super Summary | P0 | |
| Free/premium card gating | P0 | |
| Deep Dive (pre-gen + on-demand) | P0 | |
| Subscription purchase (RevenueCat) | P0 | |
| Push notifications (single timezone) | P0 | |
| Read as one | P0 | Depends on Deep Dive pre-gen (M8-equivalent) |
| Preference editing | P1 | Needed soon after launch; not launch-blocking if onboarding is a one-time flow for the first cohort |
| Admin operational tooling (Section 15) | P1 | Needed to operate safely, but can trail initial build by a few days if manual DB access substitutes short-term |
| Personalized archive | P2 | Scope undefined (Section 3) |
| Multi-timezone batching | P2 | Explicitly deferred |
| Content moderation on onboarding input | P2 (or higher — pending legal/policy review) | Currently undecided, not merely deprioritized |
| Admin analytics/charting | P2 | |

---

## 18. Acceptance Criteria

| Feature | Acceptance criteria |
|---|---|
| Onboarding extraction | Given a valid paragraph, returns `search_queries` (5-8), `thematic_tags` (4-8), one of the 5 fixed `tone_bucket` values, and `exclude_keywords` (may be empty) as strict JSON. Given an invalid/empty paragraph, no LLM call is made and a validation error is returned. |
| Preference confirmation | Editing/removing a chip and confirming persists exactly the edited version, not the original extraction. Confirmation failure preserves the user's edits client-side. |
| Card generation | For a given cluster and tone_bucket, exactly one Card row exists after any number of requests for that combination (FR-GEN-1 verified via row count, not call count, for black-box testing). |
| Super Summary | For a given `cluster_set_key` + `tone_bucket`, exactly one row exists regardless of how many users share that combination. Synthesis is 150-250 words and references only the provided clusters. |
| Deep Dive pre-generation | After a batch run, every cluster appearing in any user's top-6 set has a `deep_dives` row with `pre_generated = true`. |
| Deep Dive on-demand | First request for a long-tail cluster creates exactly one `deep_dives` row; a second request for the same cluster returns without a new generation call. |
| Free-tier card gating | A free user can retrieve exactly 5 distinct cards per calendar day; the 6th request is rejected server-side regardless of client state. |
| Free-tier Deep Dive gating | Any Deep Dive request from a free-tier user (via UI or direct API call) is rejected server-side. |
| Subscription unlock | A successful RevenueCat webhook for a given user results in that user's next `GET /briefing/today` and `POST /deep-dive` calls reflecting premium access, with no manual intervention. |
| Read as one | Renders only clusters with `pre_generated = true` in `deep_dives`; issues zero calls to the on-demand Deep Dive endpoint under any circumstance. |
| Notifications | Daily notification is sent to every user with a valid `expo_push_token` after batch completion, referencing the top Deep Dive story's title. |
| Batch idempotency | Re-running the batch job for a `batch_date` that already completed produces no duplicate rows in `news_clusters`, `cards`, `super_summaries`, or `deep_dives`. |

---

## 19. Deployment & Infrastructure

`[OPEN DECISION on all vendor choices below — requirements are stated vendor-neutral where possible]`

- Backend must run as a containerized service with headroom for horizontal scaling, even though MVP targets a single instance.
- **Scheduler constraint (not open):** if the hosting choice is multi-instance or serverless, APScheduler must be replaced with an external cron trigger — running the in-process scheduler on multiple instances will duplicate the batch job and its LLM cost.
- Managed Postgres and managed Redis are assumed over self-hosted, for operational simplicity — specific providers not chosen.
- Mobile builds via Expo EAS Build (standard tooling for the already-decided Expo platform, not a new open decision).
- CI/CD pipeline: undecided.
- Secrets management: environment variables are the confirmed minimum (Section 10.3); a dedicated secrets manager is undecided.
- App Store / Play Store submission requirements (privacy nutrition labels, data collection disclosures) have not been reviewed against this product's actual data collection — required before submission, not before development.

---

## 20. Assumptions & Open Decisions (Consolidated)

**Genuinely undecided — needs a decision before or during build:**
- Authentication mechanism and session strategy (Section 10.2)
- Preference-edit flow and its endpoint (`PUT /preferences`) (Sections 4.1, 6.8, 7.2)
- Personalized archive scope, retention window, and UI (Sections 3, 7.2, 12)
- Admin dashboard exact scope and access-control mechanism (Section 15)
- Content moderation policy for onboarding paragraphs (Section 14)
- GDPR/CCPA compliance posture (Section 10.4)
- Hosting provider, managed DB/Redis provider, CI/CD pipeline, secrets manager (Section 19)
- RevenueCat reconciliation job (proposed, not confirmed as in-scope) (Section 11)
- Client behavior during the payment-success/webhook-delay window (Section 14)
- Exact rate-limit thresholds for LLM-cost-bearing endpoints (Section 10.3)

**Deferred by decision, not undecided (explicitly out of MVP scope):**
- Multi-timezone batch cohorting
- On-demand fallback generation inside "Read as one" for long-tail stories
- Admin analytics/charting
- Localization beyond English

**Proposed defaults used elsewhere in this document for concreteness (flagged inline, listed here for visibility):**
- Minimum onboarding paragraph length: 20 characters
- Default `tone_bucket` fallback on repeated extraction failure: `high_signal`
- Single device per user for push tokens
- Sub-second target response time for `GET /briefing/today`
