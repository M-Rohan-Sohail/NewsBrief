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

---

## Phase 5: Pre-Beta Polish & Hardening
- `[x]` **Purge Broken Native Import:** Remove `import Purchases, { PurchasesPackage } from 'react-native-purchases';` from `frontend/src/context/RevenueCatContext.tsx`.
- `[x]` **Fix ARQ Slack Task Serialization:** Cast `str(inst.team_id)` and add `if inst.team_id:` guard in `backend/worker.py` (`dispatch_hourly_deliveries_task`).
- `[x]` **Add Email Briefing Fallback:** Update `backend/services/email_service.py` to fall back to latest briefing if today's batch is not yet generated.
- `[x]` **Deduplicate Test Client Setup:** Remove duplicated test client setup lines in `backend/tests/test_admin_endpoints.py`.
- `[x]` **Align Token Access in AuthContext & FeedbackModal:** Expose `getToken` in `frontend/src/context/AuthContext.tsx` and ensure `frontend/src/components/FeedbackModal.tsx` retrieves token without runtime `TypeError`.
- `[x]` **Verification:** Run `python3 -m py_compile` across all backend modules and verify zero syntax errors.

---

## Phase 6: Android APK Stability, Expo 57 Native Compatibility & Startup Crash Resolution
- `[x]` **Fix Metro Bundler Failures:**
  - Provide `frontend/shims/punycode.js` and configure `frontend/metro.config.js` to resolve `markdown-it` punycode requirement.
  - Safely stub `registerForPushNotificationsAsync` in `frontend/src/context/AuthContext.tsx` to prevent uninstalled dynamic import failures.
- `[x]` **Migrate Deprecated Media Module to `expo-audio`:**
  - Replace `expo-av` with `expo-audio` (`^57.0.5`) in `frontend/package.json` to eliminate the `Unresolved reference 'resolveView'` Kotlin crash in Expo 57 / React Native 0.86.
  - Register `"expo-audio"` in `frontend/app.json` plugins.
  - Refactor `frontend/src/components/AudioPlayer.tsx` to use `useAudioPlayer` and `useAudioPlayerStatus`.
- `[x]` **Install Missing Native Peer Dependency (`expo-asset`):**
  - Add `"expo-asset": "^57.0.18"` directly to `frontend/package.json` as required by `expo-audio` to prevent Android `NoClassDefFoundError` / immediate startup crash.
- `[x]` **Resolve `app.json` Schema Validation:**
  - Remove invalid property `usesCleartextTraffic` from `android` configuration in `frontend/app.json`.
- `[x]` **Align Expo SDK Patch Version:**
  - Update `expo` dependency from `~57.0.23` to `~57.0.24` in `frontend/package.json`.
- `[x]` **Verification:**
  - Run `npx -y expo-doctor` in `frontend/` $\rightarrow$ **21/21 checks passed. No issues detected!**
  - Run `npx expo export --platform android` $\rightarrow$ **Clean Hermes bundle exported (code 0)**.

---

## Phase 7: Mobile Authentication Hardening & Standalone APK Runtime Crash Prevention
- `[x]` **Harden `LoginScreen.tsx` Google Auth Invariant:**
  - In `frontend/src/screens/LoginScreen.tsx`, supply `clientId` and `androidClientId` to `Google.useAuthRequest` so `invariantClientId` never throws on Android.
- `[x]` **Add Beta Tester Login Flow in `LoginScreen.tsx`:**
  - Add a "Continue as Beta Tester" option so testers and developers can authenticate directly without requiring Google Cloud Console OAuth registration.
- `[x]` **Configure Standalone URL Scheme in `frontend/app.json`:**
  - Add `"scheme": "newsbrief"` to `frontend/app.json` under `"expo"` to ensure deep linking and redirect URI creation succeed on native APKs.
- `[x]` **Implement Global `ErrorBoundary` in `frontend/App.tsx`:**
  - Wrap `<NavigationContainer>` in `App.tsx` with a React Error Boundary to catch any runtime exceptions gracefully and show an actionable recovery screen instead of terminating the app.
- `[x]` **Enable Beta Session Support in `backend/main.py`:**
  - In `POST /auth/google`, accept `id_token` starting with `beta_` to return a valid JWT token and user ID for beta testing.
- `[x]` **Verification:**
  - Run `npx -y expo-doctor` to confirm schema and peer dependencies $\rightarrow$ **21/21 checks passed!**
  - Run `npx expo export --platform android` to verify Hermes bundling $\rightarrow$ **Clean Hermes bytecode generated (code 0)**.

---

## Phase 8: Android Cleartext (HTTP) Network Communication
- `[x]` **Install `expo-build-properties`:**
  - Add `"expo-build-properties": "~57.0.21"` to `frontend/package.json`.
- `[x]` **Configure Cleartext Traffic in `frontend/app.json`:**
  - Add `expo-build-properties` under `plugins` with `android.usesCleartextTraffic: true`.
- `[x]` **Verification:**
  - Validate config and export Hermes bundle: `EXPO_NO_TELEMETRY=1 EXPO_OFFLINE=1 npx expo export --platform android` $\rightarrow$ **Bundled 988 modules cleanly (code 0)**.

---

## Phase 9: Frontend Preference Onboarding Routing & EAS Over-The-Air (OTA) Updates
- `[x]` **Add Preference Status to Backend `/me`:**
  - Update `GET /me` in `backend/main.py` to query `models.UserPreference` and return `has_preferences: bool`.
- `[x]` **Implement Frontend Intelligent Onboarding Routing:**
  - In `frontend/src/context/AuthContext.tsx` or `frontend/App.tsx`, check `has_preferences` upon login and navigate directly to `OnboardingScreen` if false.
- `[x]` **Enhance Empty State in `HomeScreen.tsx`:**
  - In `HomeScreen.tsx`, if `/briefing/today` returns 404, display a prominent "Set Up Your Preferences" action button routing directly to `OnboardingScreen`.
- `[x]` **Install & Configure `expo-updates`:**
  - Install `expo-updates` in `frontend/package.json`.
  - Configure `updates.url` (`https://u.expo.dev/d409abca-a70e-4a61-9af9-eecb79b44546`) and `runtimeVersion` in `frontend/app.json`.
  - Configure `"channel": "preview"` under `build.preview` in `frontend/eas.json`.
- `[x]` **Verification:**
  - Run Hermes bundling `EXPO_NO_TELEMETRY=1 EXPO_OFFLINE=1 npx expo export --platform android` to confirm clean compilation with `expo-updates`.
