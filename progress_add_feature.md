# NewsBrief Beta Features Progress Tracker

This progress tracker accompanies [`add_feature.md`](file:///home/rohan/Desktop/StartupX/add_feature.md). It outlines the implementation steps for **Checkpoint 1 (CP-26: Beta Feedback & Upvoting Board)** and **Checkpoint 2 (CP-27: Multi-Channel Engagement Analytics)**.

---

## Checkpoint 1 (CP-26): Beta Tester Feedback & Upvoting Board

### Backend & Database
- `[x]` **Define Feedback Models:** Add `BetaFeedback` and `FeedbackVote` models to `backend/models.py` with unique constraint for user votes.
- `[x]` **Add Feedback Schemas:** Define `FeedbackCreate`, `FeedbackResponse`, `FeedbackStatusUpdate` in `backend/schemas.py`.
- `[x]` **Implement Feedback Router:** Create `backend/routers/feedback_router.py` with `GET /feedback`, `POST /feedback`, `POST /feedback/{id}/vote`, and `PATCH /admin/feedback/{id}/status`.
- `[x]` **Mount Feedback Router:** Include `feedback_router` in `backend/main.py`.
- `[x]` **Unit Tests:** Implement `backend/tests/test_feedback.py` covering submission, listing, upvoting, unvoting, and admin status updates.

### Frontend UI & Admin Dashboard
- `[x]` **Build Feedback Modal Component:** Create `frontend/src/components/FeedbackModal.tsx` with Top Voted / Recent filtering, upvote button, category badges, and submission form.
- `[x]` **Integrate into HomeScreen:** Add `💡 Feedback` button in `frontend/src/screens/HomeScreen.tsx` header to open `FeedbackModal`.
- `[x]` **Add Feedback Section to Admin UI:** Embed Feedback Board into `backend/admin.html` with real-time status update dropdowns.
- `[x]` **Verification:** Run unit tests and verify mobile modal loads and upvotes correctly.

---

## Checkpoint 2 (CP-27): Multi-Channel Engagement Analytics Engine

### Backend & Telemetry Ingestion
- `[x]` **Add Event Log Model:** Create `UserEventLog` in `backend/models.py`.
- `[x]` **Implement Analytics Router:** Create `backend/routers/analytics_router.py` with `POST /analytics/event`, `GET /analytics/email-open`, and `GET /analytics/email-click`.
- `[x]` **Build Analytics Aggregation:** Add `GET /admin/analytics` in `backend/main.py`.
- `[x]` **Mount Router & Run Tests:** Mount in `main.py` and run `test_analytics.py`.

### Delivery Integrations & Dashboard
- `[x]` **Mobile Telemetry Service:** Create `frontend/src/services/analytics.ts` and hook into `AuthContext` (session times) and `AudioPlayer` (audio_play, audio_complete).
- `[x]` **Email & Slack Tracking:** Update `email_service.py` with tracking pixel and deep link redirects. Update `slack_router.py` to handle block actions.
- `[x]` **Admin Analytics UI:** Replace Global Telemetry in `admin.html` with Funnel, Channel Engagement, Primary Preference, and Live Activity feed.
- `[x]` **Update Slack Service with Tracking:** In `backend/routers/slack_router.py`, log interactive button clicks as `slack_click` events.
- `[x]` **Unit Tests:** Create `backend/tests/test_analytics.py` verifying event ingestion, pixel response, redirect logic, and stats aggregation.

### Frontend Telemetry & Admin Visualization
- `[x]` **Revamp Admin Dashboard with Analytics Tab:** In `backend/admin.html`, add visual channel breakdown bars (App vs Email vs Audio vs Slack), average session time, and live user activity feed.
- `[x]` **Verification:** Trigger actions across App, Email, Audio, and Slack, then inspect `/admin/analytics` to verify real-time metric updates.

---

## Final Beta Sign-off
- `[ ]` **Run All Tests:** Verify 100% pass across all unit test suites (`pytest backend/tests`).
- `[ ]` **Lint & Compilation Check:** Run `python3 -m py_compile` and verify TypeScript compilation in frontend.
