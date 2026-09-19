# NewsBrief Fix & Integration Progress Tracker

This progress tracker accompanies [`fix.md`](file:///home/rohan/Desktop/StartupX/fix.md). It outlines the sequential steps required to eliminate all architectural gaps, missing files, scheduling disconnections, and UI inconsistencies.

---

## Phase 1: Task Queue & Docker Worker Stability
- `[x]` **Add Queue Dependencies:** Add `arq==0.26.1` and `redis==5.2.1` to `backend/requirements.txt`.
- `[x]` **Implement Worker Entrypoint:** Create `backend/worker.py` with `WorkerSettings`, async tasks (`run_stage1_pipeline_task`, `run_stage2_pipeline_task`, `send_email_digest_task`, `post_slack_briefing_task`, `dispatch_hourly_deliveries_task`), and cron schedules.
- `[x]` **Write Worker Unit Tests:** Create `backend/tests/test_worker_tasks.py` verifying task definitions and execution logic using mocks.
- `[x]` **Verification:** Run `python3 -c "import sys; sys.path.insert(0, 'backend'); from worker import WorkerSettings; print('Worker loaded:', [f.__name__ for f in WorkerSettings.functions])"`.

---

## Phase 2: Pipeline Orchestration & Delivery Wiring
- `[x]` **Overhaul Nightly Scheduler:** Replace legacy `daily_pipeline_job` in `backend/main.py` with the two-stage execution sequence (`pipeline_stage1.run_stage1()` $\rightarrow$ `pipeline_stage2.run_stage2()`).
- `[x]` **Wire Automated Deliveries:** In `daily_pipeline_job`, trigger `services.email_service.send_daily_digest` for enabled users and `services.slack_service.send_slack_briefing` for installed Slack workspaces.
- `[x]` **Add Admin Stage 1 Trigger:** Add endpoint `POST /admin/trigger-stage1` in `backend/main.py` to trigger Stage 1 in background tasks.
- `[x]` **Add Admin Deliveries Trigger:** Add endpoint `POST /admin/trigger-deliveries` in `backend/main.py` to dispatch daily email digests and Slack drops.
- `[x]` **Update Pipeline Trigger:** Update `POST /admin/trigger-pipeline` in `backend/main.py` to execute Stage 1 followed by Stage 2 sequentially.
- `[x]` **Add Test Email Route:** Add endpoint `POST /admin/test-email` in `backend/main.py` to send a sample rendered briefing email to an address.
- `[x]` **Verification:** Verify all new routes are mounted in `backend/main.py` and accept `key=mysecret` authentication.

---

## Phase 3: Admin Dashboard 2.0 & Telemetry
- `[x]` **Expand Telemetry Endpoint:** Update `GET /admin/stats` in `backend/main.py` to return source health status (Hacker News, GitHub, arXiv, RSS), cluster counts, team counts, Slack installs, and audio generation metrics.
- `[x]` **Revamp Admin UI:** Overhaul `backend/admin.html` with Tailwind CSS, source health indicator cards, audio telemetry, and operational trigger buttons (Stage 1, Stage 2, Deliveries, Test Email).
- `[x]` **Implement Admin Test Suite:** Create `backend/tests/test_admin_endpoints.py` testing `GET /admin`, `GET /admin/stats`, and trigger routes with and without authentication keys.
- `[x]` **Verification:** Load `/admin?key=mysecret` in browser or curl endpoint to verify live telemetry rendering.

---

## Phase 4: Frontend API Centralization & Email Settings
- `[x]` **Centralize API Configuration:** Create `frontend/src/config.ts` exporting `API_URL` based on `Platform.OS`.
- `[x]` **Refactor Screens:** Update `LoginScreen.tsx`, `HomeScreen.tsx`, `CardModeScreen.tsx`, `DeepDiveScreen.tsx`, `ReadAsOneScreen.tsx`, `PreferenceConfirmationScreen.tsx` to import `API_URL`.
- `[x]` **Create Email Preferences Modal:** Build `frontend/src/components/EmailPreferencesModal.tsx` to read (`GET`) and update (`PUT`) `/users/me/email-preferences` (fields: `daily_digest_enabled`, `delivery_time`).
- `[x]` **Integrate Modal:** Add an "Email Settings" button (gear icon) in `frontend/src/screens/HomeScreen.tsx` header to trigger the `EmailPreferencesModal`.
- `[x]` **Verification:** Run `npm test` or start Expo to verify clean compilation with no hardcoded URLs or broken imports.
