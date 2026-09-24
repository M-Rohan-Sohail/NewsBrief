# NewsBrief: Codebase Fix & Integration Specification

**Target Repository:** `/home/rohan/Desktop/StartupX`  
**Target Agent:** Google Antigravity IDE  
**Document Purpose:** Complete, zero-assumption engineering specification to resolve all architectural disconnects, missing files, scheduling gaps, and frontend inconsistencies across the NewsBrief codebase.  
**Companion Tracker:** [`fix_progress.md`](file:///home/rohan/Desktop/StartupX/fix_progress.md)

---

## 1. Executive Summary of Detected Issues

Following the initial completion of Checkpoints 1 through 25, an in-depth codebase audit identified 4 critical architectural gaps:
1. **Container Failure in `docker-compose.yml`:** The `worker` container executes `command: arq worker.WorkerSettings`, but `backend/worker.py` was never implemented and `arq`/`redis` are missing from `backend/requirements.txt`.
2. **Scheduling Disconnect in `backend/main.py`:** The nightly scheduler in `main.py` still invokes the legacy `run_pipeline.py` (which scrapes Google News per-user), completely bypassing `pipeline_stage1.py` and `pipeline_stage2.py`. Furthermore, the delivery services (`send_daily_digest` and `send_slack_briefing`) are never triggered on schedule.
3. **Incomplete Checkpoint 25 (Admin Telemetry):** `backend/admin.html` is the v1 skeleton. It lacks source health indicators, token spend tracking, and manual trigger controls for Stage 1, Stage 2, and deliveries. `test_admin_endpoints.py` is missing.
4. **Mobile API URL Inconsistency:** Screens like `OnboardingScreen.tsx` and `LoginScreen.tsx` hardcode `http://localhost:8000` (which fails on Android emulators and physical devices), while others check `Platform.OS`. A centralized `config.ts` is required, along with UI for email preferences.

---

## 2. Phase 1: Task Queue & Docker Worker Fixes

### 2.1 Dependencies (`backend/requirements.txt`)
Ensure the following packages are present:
```text
arq==0.26.1
redis==5.2.1
```

### 2.2 Task Worker (`backend/worker.py`)
Create `backend/worker.py` to serve as the entrypoint for the `arq` worker process declared in `docker-compose.yml`.

**Required Functions & Behaviors:**
1. `run_stage1_pipeline_task(ctx)`: Invokes `pipeline_stage1.run_stage1()` to ingest multi-source feeds, deduplicate, cluster, compute centroids, and pre-generate base cards and deep dives.
2. `run_stage2_pipeline_task(ctx)`: Invokes `pipeline_stage2.run_stage2()` to perform `pgvector` user cosine matching and generate personalized super summaries.
3. `send_email_digest_task(ctx, user_id: str)`: Calls `services.email_service.send_daily_digest(user_id, db)` for a specific user.
4. `post_slack_briefing_task(ctx, team_id: str)`: Calls `services.slack_service.send_slack_briefing()` for a team's configured Slack installation.
5. `dispatch_hourly_deliveries_task(ctx)`: Queries `UserEmailPreference` where `daily_digest_enabled=True` and dispatches pending daily digest emails, plus posts active Slack briefings.
6. `WorkerSettings` class:
   - `functions`: List of the 5 task functions above.
   - `cron_jobs`:
     - Stage 1 nightly: `cron(run_stage1_pipeline_task, hour=3, minute=0, timezone="UTC")`
     - Stage 2 nightly: `cron(run_stage2_pipeline_task, hour=4, minute=0, timezone="UTC")`
     - Hourly deliveries: `cron(dispatch_hourly_deliveries_task, minute=0)`
   - `redis_settings`: `RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))`

### 2.3 Unit Testing (`backend/tests/test_worker_tasks.py`)
Ensure `backend/tests/test_worker_tasks.py` tests all tasks using `unittest.mock` to verify that `WorkerSettings` loads and tasks execute properly without connecting to a live Redis server during tests.

---

## 3. Phase 2: Pipeline Orchestration & Scheduling Wiring

### 3.1 Backend Scheduler Overhaul (`backend/main.py`)
Replace the legacy `daily_pipeline_job` with the modern two-stage pipeline and delivery cycle:

```python
def daily_pipeline_job():
    logger.info("Running scheduled Stage 1 Global Pipeline...")
    from pipeline_stage1 import run_stage1
    run_stage1()
    
    logger.info("Running scheduled Stage 2 Personalization Pipeline...")
    from pipeline_stage2 import run_stage2
    run_stage2()
    
    logger.info("Dispatching daily email digests and Slack drops...")
    from db import SessionLocal
    from models import UserEmailPreference, SlackInstallation
    from services.email_service import send_daily_digest
    from services.slack_service import build_briefing_blocks, send_slack_briefing
    from models import UserBriefing, SuperSummary, Card
    
    db = SessionLocal()
    try:
        # 1. Email delivery
        prefs = db.query(UserEmailPreference).filter(UserEmailPreference.daily_digest_enabled == True).all()
        for p in prefs:
            try:
                send_daily_digest(str(p.user_id), db)
            except Exception as e:
                logger.error(f"Failed to dispatch email to {p.user_id}: {e}")
                
        # 2. Slack delivery
        installations = db.query(SlackInstallation).all()
        today = datetime.now(timezone.utc).date()
        briefing = db.query(UserBriefing).filter(UserBriefing.batch_date == today).first()
        if briefing:
            ss = db.query(SuperSummary).filter(SuperSummary.id == briefing.super_summary_id).first()
            cards = db.query(Card).filter(Card.id.in_(briefing.card_ids)).limit(3).all()
            app_url = os.environ.get("APP_URL", "http://localhost:3000")
            blocks = build_briefing_blocks(ss, cards, app_url)
            for inst in installations:
                send_slack_briefing(inst, blocks)
    finally:
        db.close()
    logger.info("Daily scheduled pipeline and deliveries completed.")
```

### 3.2 Admin Endpoints (`backend/main.py`)
Update and add the following administrative trigger routes:
* `POST /admin/trigger-stage1`: Triggers `pipeline_stage1.run_stage1()` in background tasks.
* `POST /admin/trigger-stage2`: (Keep existing) Triggers `pipeline_stage2.run_stage2()` in background tasks.
* `POST /admin/trigger-pipeline`: Updates to run Stage 1 followed by Stage 2 sequentially.
* `POST /admin/trigger-deliveries`: Triggers email digests and Slack drops for today's briefing in background tasks.
* `POST /admin/test-email`: Accepts JSON `{"email": "user@example.com"}` and sends a sample rendered briefing email via `email_service`.

---

## 4. Phase 3: Admin Dashboard 2.0 & Telemetry

### 4.1 Enhanced Telemetry Endpoint (`GET /admin/stats` in `backend/main.py`)
Update `GET /admin/stats` to return comprehensive operational health metrics:
```python
@app.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db), is_admin: bool = Depends(verify_admin_key)):
    today = datetime.now(timezone.utc).date()
    
    total_users = db.query(models.User).count()
    premium_users = db.query(models.User).filter(models.User.subscription_status.in_(["premium", "pro", "executive"])).count()
    briefings_today = db.query(models.UserBriefing).filter(models.UserBriefing.batch_date == today).count()
    cards_today = db.query(models.Card).filter(db.func.date(models.Card.generated_at) == today).count()
    clusters_today = db.query(models.NewsCluster).filter(models.NewsCluster.batch_date == today).count()
    teams_count = db.query(models.Team).count()
    slack_installs = db.query(models.SlackInstallation).count()
    audio_generated = db.query(models.SuperSummary).filter(
        models.SuperSummary.batch_date == today,
        models.SuperSummary.audio_url.isnot(None)
    ).count()

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "briefings_today": briefings_today,
        "cards_today": cards_today,
        "clusters_today": clusters_today,
        "teams_count": teams_count,
        "slack_installs": slack_installs,
        "audio_generated": audio_generated,
        "sources_health": {
            "hacker_news": {"status": "active"},
            "github_trending": {"status": "active"},
            "arxiv_papers": {"status": "active"},
            "rss_feeds": {"status": "active"}
        }
    }
```

### 4.2 Dashboard UI (`backend/admin.html`)
Revamp `backend/admin.html` with modern styling (Tailwind CSS CDN) containing:
1. **Header:** Title, API status indicator, secret key query pass-through.
2. **Telemetry Grid:** Total Users, Premium/Pro Users, Teams, Clusters Formed Today, Cards Today, Audio Briefings Today.
3. **Data Source Health Cards:** Status badges for Hacker News, GitHub Trending, arXiv, and Substack RSS.
4. **Action Control Panel:**
   - Button: *Run Stage 1 (Global Ingestion & Clustering)* -> `POST /admin/trigger-stage1`
   - Button: *Run Stage 2 (User Personalization)* -> `POST /admin/trigger-stage2`
   - Button: *Dispatch Deliveries (Email & Slack)* -> `POST /admin/trigger-deliveries`
   - Input + Button: *Send Test Email* -> `POST /admin/test-email`
5. **Live Status Message Bar:** Renders success/error state of triggered actions.

### 4.3 Automated Admin Tests (`backend/tests/test_admin_endpoints.py`)
Create unit tests validating:
- `GET /admin` returns 200 with HTML content.
- `GET /admin/stats?key=mysecret` returns 200 with complete telemetry schema.
- `POST /admin/trigger-stage1?key=mysecret` triggers task and returns 200.
- Unauthorized requests without `key=mysecret` return 403 Forbidden.

---

## 5. Phase 4: Frontend API Centralization & Email Settings

### 5.1 Centralized API Configuration (`frontend/src/config.ts`)
Create `frontend/src/config.ts`:
```typescript
import { Platform } from 'react-native';

export const API_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';
```
Replace all fragmented instances of `http://localhost:8000`, `10.0.2.2`, or `127.0.0.1` across:
- `frontend/src/screens/OnboardingScreen.tsx`
- `frontend/src/screens/LoginScreen.tsx`
- `frontend/src/screens/HomeScreen.tsx`
- `frontend/src/screens/CardModeScreen.tsx`
- `frontend/src/screens/DeepDiveScreen.tsx`
- `frontend/src/screens/ReadAsOneScreen.tsx`
- `frontend/src/screens/PreferenceConfirmationScreen.tsx`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/context/RevenueCatContext.tsx`

### 5.2 Email Preferences Modal (`frontend/src/components/EmailPreferencesModal.tsx`)
Create a modal component allowing users to:
1. Toggle `daily_digest_enabled` (Switch component).
2. Set preferred delivery time string (e.g. `06:30`, `07:00`, `08:00`).
3. Fetch initial state from `GET /users/me/email-preferences`.
4. Save updates via `PUT /users/me/email-preferences`.
5. Embed access button (e.g. ✉️ *Email Digest Settings*) in `HomeScreen.tsx` header or menu.

---

## 6. Phase 5: Pre-Beta Polish & Hardening

### 6.1 Purge Broken Native Import (`frontend/src/context/RevenueCatContext.tsx`)
Remove the unused import from `frontend/src/context/RevenueCatContext.tsx`:
```typescript
import Purchases, { PurchasesPackage } from 'react-native-purchases';
```
Since `react-native-purchases` is not installed in `package.json` (mock types are used instead), retaining this import causes Metro bundler to fail during `npx expo start` with `Unable to resolve module 'react-native-purchases'`.

### 6.2 ARQ Task Serialization & Null Safety (`backend/worker.py`)
In `dispatch_hourly_deliveries_task` in `backend/worker.py`, ensure Slack briefing tasks safely handle UUID serialization and unassigned teams:
```python
        # Slack deliveries
        installations = db.query(SlackInstallation).all()
        for inst in installations:
            try:
                if inst.team_id:
                    await ctx['redis'].enqueue_job('post_slack_briefing_task', str(inst.team_id))
            except Exception as e:
                logger.error(f"Failed to enqueue slack briefing for {inst.team_id}: {e}")
```
ARQ's msgpack serializer cannot serialize raw Python `uuid.UUID` objects. Casting to `str(inst.team_id)` and verifying `inst.team_id` is not `None` prevents unhandled serialization exceptions.

### 6.3 Graceful Briefing Fallback for Digest Previews (`backend/services/email_service.py`)
In `send_daily_digest` (`backend/services/email_service.py`), fall back to the most recent user briefing if today's batch has not yet generated:
```python
    # Fetch User Briefing (today or latest available fallback)
    briefing = db.query(UserBriefing).filter(
        UserBriefing.user_id == user.id,
        UserBriefing.batch_date == today
    ).first()
    
    if not briefing:
        briefing = db.query(UserBriefing).filter(
            UserBriefing.user_id == user.id
        ).order_by(UserBriefing.batch_date.desc()).first()
```
This ensures `/admin/test-email` and manual previews always deliver a sample email without requiring the 3:00 AM nightly cron batch to have already executed.

### 6.4 Clean Duplicate Setup in Tests (`backend/tests/test_admin_endpoints.py`)
In `backend/tests/test_admin_endpoints.py`, remove the redundant lines 21–29 that duplicate `client = TestClient(app)` and `app.dependency_overrides[get_db] = override_get_db`.

### 6.5 Align Token Access in AuthContext & FeedbackModal (`frontend/src/context/AuthContext.tsx` & `frontend/src/components/FeedbackModal.tsx`)
In `frontend/src/components/FeedbackModal.tsx`, the component attempts to invoke `const { getToken } = useAuth(); await getToken();`, but `AuthContext.tsx` only exposes `{ accessToken, userId, isLoading, signIn, signOut }`, resulting in a runtime crash `TypeError: getToken is not a function`.

**Required Fix:**
1. In `frontend/src/context/AuthContext.tsx`:
   - Extend `AuthContextType` with `getToken: () => Promise<string | null>;`.
   - Implement `const getToken = async () => accessToken || (await AsyncStorage.getItem('access_token'));`.
   - Pass `getToken` into `<AuthContext.Provider value={{ accessToken, userId, isLoading, signIn, signOut, getToken }}>`.
2. In `frontend/src/components/FeedbackModal.tsx`:
   - Consume `{ accessToken, getToken } = useAuth();`.
   - Use `accessToken || (await getToken())` for API request Authorization headers (`Bearer ${token}`).

---

## 7. Phase 6: Android APK Stability & Startup Crash Resolution

### 7.1 Root Causes of Startup Crash & Build Errors
1. **Missing Peer Dependency (`expo-asset`):** `expo-audio` requires `expo-asset` to be installed directly in root project dependencies for native autolinking into Android's `PackageList.java`. Without it, Android throws `ClassNotFoundException` / `NoClassDefFoundError` upon launching, causing the APK to immediately close.
2. **Schema Invalidation in `app.json`:** `android.usesCleartextTraffic` is not a valid property in Expo's `app.json` schema, failing `expo-doctor` schema verification.
3. **Expo SDK Version Alignment:** `expo` package was on `~57.0.23` while SDK required `~57.0.24`.
4. **Legacy Media Module Deprecation:** `expo-av` failed Kotlin compilation with `Unresolved reference 'resolveView'` because `UIManager.resolveView` was removed in Expo 57 / React Native 0.86 New Architecture (Fabric).
5. **Metro Static Resolution for Push Notifications & Punycode:** Dynamic imports of uninstalled `expo-notifications` and unshimmed `punycode` in `markdown-it` crashed Metro bundler during `:app:createBundleReleaseJsAndAssets`.

### 7.2 Required Fixes & Implementation
1. **Install `expo-asset` & Align Expo Version:**
   In `frontend/package.json`, add `"expo-asset": "^57.0.18"` and update `"expo": "~57.0.24"`.
2. **Purge Schema Errors in `app.json`:**
   Remove `usesCleartextTraffic` from `android` object in `frontend/app.json`.
3. **Modernize Audio System to `expo-audio`:**
   Replace legacy `expo-av` with `expo-audio` (`^57.0.5`) in `package.json`, register `"expo-audio"` in `app.json` plugins, and update `AudioPlayer.tsx` to use `useAudioPlayer` and `useAudioPlayerStatus`.
4. **Metro Punycode Shim & AuthContext Stub:**
   Provide `frontend/shims/punycode.js` mapped in `frontend/metro.config.js`, and stub `registerForPushNotificationsAsync` safely in `AuthContext.tsx`.

---

## 8. Phase 7: Mobile Authentication Hardening & Standalone APK Runtime Crash Prevention

### 8.1 Root Causes of Runtime Crash on App Launch
1. **Uncaught Synchronous Exception in `Google.useAuthRequest`:**
   - In `frontend/src/screens/LoginScreen.tsx`, `Google.useAuthRequest({ webClientId: 'dummy_google_client_id...' })` is invoked on initial render.
   - On Android, `expo-auth-session/providers/google` evaluates `Platform.select({ android: 'androidClientId', ... })` and checks `config['androidClientId'] ?? config.clientId`.
   - Because only `webClientId` is passed, `clientId` evaluates to `undefined`.
   - `invariantClientId('androidClientId', undefined, 'Google')` in `ProviderUtils.js` synchronously executes:
     `throw new Error("Client Id property 'androidClientId' must be defined to use Google auth on this platform.")`
   - In production APK release builds, this uncaught exception during the initial render pass terminates the React Native Android host process immediately upon launching.

2. **Missing Standalone URL Scheme in `app.json`:**
   - Standalone APK builds require `"scheme"` in `app.json` (e.g. `"scheme": "newsbrief"`) for deep linking and OAuth redirect URI construction.
   - Without `"scheme"`, `AuthSession.makeRedirectUri()` throws `"Cannot make a deep link into a standalone app with no custom scheme defined"`.

3. **Missing Beta Tester / Developer Login Flow:**
   - The app only provides a "Sign in with Google" button that depends on Google Cloud Console OAuth 2.0 Client ID registration (with SHA-1 release keystore fingerprint).
   - Beta testers and developers cannot authenticate without Google Cloud setup. A fallback "Continue as Beta Tester" login flow is required to exchange authentication credentials with the backend `/auth/google` or establish a test session.

4. **Absence of Top-Level React Error Boundary:**
   - In `frontend/App.tsx`, there is no `ErrorBoundary` wrapping `<NavigationContainer>`. Any unexpected JavaScript runtime exception crashes the entire Android app to the home screen instead of rendering an actionable error recovery screen.

### 8.2 Required Fixes & Implementation
1. **Harden `LoginScreen.tsx` Authentication:**
   - In `frontend/src/screens/LoginScreen.tsx`, supply fallback `clientId` and `androidClientId` properties so `useAuthRequest` never throws an invariant error on Android:
     ```typescript
     const [request, response, promptAsync] = Google.useAuthRequest({
       clientId: 'dummy_client_id',
       androidClientId: 'dummy_client_id.apps.googleusercontent.com',
       webClientId: 'dummy_google_client_id.apps.googleusercontent.com',
     });
     ```
   - Add a **"Continue as Beta Tester"** button that generates or provides a beta user token and signs in immediately via `signIn(token, user_id)`:
     ```typescript
     const handleBetaLogin = async () => {
       try {
         const res = await fetch(`${API_URL}/auth/google`, {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ id_token: 'beta_tester_token' })
         });
         const data = await res.json();
         if (data.access_token) {
           await signIn(data.access_token, data.user_id);
           return;
         }
       } catch (err) {
         console.warn("Backend auth failed, using local session:", err);
       }
       await signIn('beta_test_access_token', 'beta_user_1');
     };
     ```
2. **Add URL Scheme in `frontend/app.json`:**
   - Under `"expo"`, add `"scheme": "newsbrief"`.
3. **Implement Root `ErrorBoundary` in `frontend/App.tsx`:**
   - Create an `ErrorBoundary` React component that catches rendering errors and displays an error message with a "Restart App" button instead of crashing the native process.
4. **Backend Beta Token Fallback in `backend/main.py`:**
   - In `backend/main.py` `/auth/google`, allow testing bypass when `request.id_token.startswith("beta_")`, returning a valid JWT session for `beta_tester@startupx.com`.

---

## 9. Phase 8: Android Cleartext (HTTP) Communication Permission

### 9.1 Root Cause of Network Error
When testing against a self-hosted backend over raw IP and unencrypted HTTP (e.g. `http://13.50.57.65:8000`), Android 9+ (API Level 28+) network security configuration rejects all plain HTTP requests by default, throwing:
`fetch failed: java.net.UnknownServiceException: CLEARTEXT communication to 13.50.57.65 not permitted by network security rules`

Adding `usesCleartextTraffic` directly under `expo.android` in `app.json` violates Expo config schema validation. The standard and verified mechanism in Expo is through the `expo-build-properties` plugin.

### 9.2 Required Fixes & Implementation
1. **Install `expo-build-properties`:**
   Add `"expo-build-properties": "~57.0.21"` to `frontend/package.json`.
2. **Configure Config Plugin in `frontend/app.json`:**
   Under `"plugins"` in `frontend/app.json`:
   ```json
   [
     "expo-build-properties",
     {
       "android": {
         "usesCleartextTraffic": true
       }
     }
   ]
   ```
3. **Rebuild Native Android Binary:**
   Because `expo-build-properties` modifies the native `AndroidManifest.xml` during native prebuild (`android:usesCleartextTraffic="true"`), a fresh APK rebuild with EAS (`eas build -p android --profile preview`) is required.

---

## 10. Phase 9: Frontend Preference Onboarding Routing & EAS Over-The-Air (OTA) Updates

### 10.1 Root Causes of Navigation Disconnect & Build Overhead
1. **Onboarding Routing Disconnect:**
   - In `frontend/App.tsx`, once `accessToken` is established (after Google sign-in or "Continue as Beta Tester"), React Navigation immediately mounts the first screen in the authenticated stack, which is `HomeScreen.tsx`.
   - `HomeScreen.tsx` immediately attempts `GET /briefing/today`.
   - For a brand new user, guest, or beta tester without a pre-generated briefing in Postgres, `/briefing/today` returns HTTP 404 (`"No briefing found. Please ensure you have set your preferences..."`) or throws a network exception.
   - `HomeScreen.tsx` displays either an error ("Failed to fetch briefing") or an empty state ("Your first briefing is being generated") instead of welcoming the user to configure their news preferences.
   - The user is never automatically routed to `OnboardingScreen.tsx` ("What do you care about?") to set up their preference profile.

2. **Absence of Over-The-Air (OTA) Update Capability:**
   - Standalone APKs built without `expo-updates` do not contain the native background listener needed to download new JavaScript bundles from Expo Application Services (EAS).
   - Every small frontend UI, text, or navigation fix currently requires running a full native Android cloud rebuild (`eas build -p android --profile preview`), which is slow and requires manually reinstalling the APK on the device.
   - Installing `expo-updates` and configuring `"channel": "preview"` enables immediate Over-The-Air updates via `eas update`, allowing all future frontend bug fixes to deploy in seconds without rebuilding or reinstalling the APK.

### 10.2 Required Fixes & Implementation
1. **Backend User Preferences Status (`backend/main.py`):**
   - Update `GET /me` in `backend/main.py` to check `db.query(models.UserPreference).filter(models.UserPreference.user_id == current_user.id).first()`.
   - Return `has_preferences: bool` in the response payload so the client knows whether the user has completed onboarding.

2. **Frontend Intelligent Route Resolution:**
   - In `frontend/src/context/AuthContext.tsx` or `frontend/App.tsx`, check `has_preferences` after sign-in.
   - If `has_preferences === false`, navigate directly to `OnboardingScreen` ("What do you care about?").
   - In `frontend/src/screens/HomeScreen.tsx`, if `/briefing/today` returns 404 and `has_preferences` is false, automatically redirect to `Onboarding` or render a prominent "Set Up Your Preferences" button that takes the user directly to `OnboardingScreen`.

3. **Install & Configure `expo-updates`:**
   - Install `expo-updates` in `frontend/package.json`.
   - In `frontend/app.json`:
     - Add `"updates": { "url": "https://u.expo.dev/d409abca-a70e-4a61-9af9-eecb79b44546" }`.
     - Add `"runtimeVersion": { "policy": "appVersion" }`.
   - In `frontend/eas.json`:
     - Under `build.preview`, add `"channel": "preview"`.
     - Under `build.production`, add `"channel": "production"`.

4. **One-Time Rebuild for Native OTA Support:**
   - Rebuild the APK one final time (`eas build -p android --profile preview`) to embed `expo-updates` native binaries into the APK.
   - Subsequent frontend changes will be pushed instantly via `eas update --channel preview --message "..."`.

---

## 11. Phase 10: Real-Time Beta Onboarding, Custom Delivery Email & On-Demand Briefing Pipeline

### 11.1 Problem Statement & Objectives
1. **Beta Tester Onboarding First-Contact Experience:**
   - A fresh beta tester signing in must be routed directly to the Preference setup flow (`OnboardingScreen.tsx` - "What do you care about?") rather than landing on the empty `HomeScreen`.
2. **Beta Tester Delivery Email Registration:**
   - Because beta testers log in without standard passwords or Google OAuth profiles, they must be able to specify their own delivery email address during the preference confirmation step.
   - This email is stored on `User.email` and `UserEmailPreference` so Resend sends digest briefings to their actual email inbox.
3. **On-Demand Real-Time Briefing Generation with Feedback Spinner:**
   - Rather than waiting for the nightly cron (which runs at 3 AM/4 AM UTC), the app must immediately personalize and generate the user's first briefing in real time.
   - While generating, the app displays a dedicated progress experience: *"Setting you up... Personalizing your briefing..."*
   - Once completed, the app displays the generated briefing immediately, triggers the initial daily digest email via Resend in the background, and readies the audio briefing in the background.
4. **Slack Scope:**
   - Keep Slack notifications in demo mode (skipped for on-demand beta onboarding).

### 11.2 Required Fixes & Implementation
1. **Backend Email & On-Demand Briefing Endpoints (`backend/main.py`):**
   - Update `schemas.OnboardingConfirmRequest` to include optional `email: Optional[EmailStr] = None`.
   - In `POST /onboarding/confirm`:
     - If `request.email` is supplied, update `current_user.email = request.email` and upsert `UserEmailPreference(user_id=current_user.id, daily_digest_enabled=True)`.
   - Add endpoint `POST /briefing/generate-now`:
     - Accepts authenticated `current_user`.
     - Checks if today's `NewsCluster` records exist; if missing, triggers `pipeline_stage1.run_stage1()` to populate base clusters.
     - Computes `preference_embedding` for `current_user` and performs `pgvector` cosine matching to find the top 6 clusters.
     - Retrieves or generates cards matching the user's selected `tone_bucket`.
     - Generates the `SuperSummary` using Groq LLM (or reuses existing matching summary).
     - Persists `UserBriefing(user_id=current_user.id, batch_date=today, super_summary_id=..., card_ids=...)`.
     - In `BackgroundTasks`: dispatches `services.email_service.send_daily_digest(current_user.id, db)` and audio generation.
     - Returns `schemas.BriefingResponse` with the newly generated super summary and cards.

2. **Frontend Navigation & Initial Route Resolution (`frontend/App.tsx` & `AuthContext.tsx`):**
   - In `frontend/src/context/AuthContext.tsx`, expose `setHasPreferences` in `AuthContextType` so screens can update onboarding status reactively.
   - In `frontend/App.tsx`:
     - Read `hasPreferences` from `useAuth()`.
     - Configure `initialRouteName={hasPreferences ? "Home" : "Onboarding"}` in `Stack.Navigator`.

3. **Frontend Preference & Email Input Flow (`PreferenceConfirmationScreen.tsx`):**
   - Add an Email Input section:
     - Header: *"Where should we send your daily briefing?"*
     - Input: Email address field (prefilled if user email is not the placeholder `beta_tester@startupx.com`).
     - Note: *"Enter your email to receive morning briefing digests."*
   - Implement the *"Setting you up..."* Loading State:
     - When the user taps **"Generate My Briefing"**, show an animated loading view:
       - Spinner with gradient styling.
       - Title: *"Setting you up..."*
       - Subtitle: *"Personalizing your briefing based on your topics and tone..."*
     - Calls `POST /onboarding/confirm` (including email).
     - Calls `POST /briefing/generate-now`.
     - Once response returns with cards, updates `setHasPreferences(true)` and navigates to `Home` with the live briefing preloaded.

4. **LLM Input & Context Window Guardrails (`generation.py` & `pipeline.py`):**
   - Prevent Groq `413 / Request too large for model 'qwen/qwen3.8-27b' (OTPM Limit)` errors:
     - In `pipeline.py` (`extract_preferences_from_paragraph`): Truncate input paragraph to max 1,000 characters.
     - In `generation.py` (`generate_card`): Bound article content per source to max 300 characters, capping total context at 1,200 characters (~300 tokens).
     - In `generation.py` (`generate_super_summary`): Bound each story snippet to max 150 characters, capping overall prompt context at 1,000 characters (~250 tokens).
     - In `generation.py` (`generate_deep_dive`): Cap combined article text to max 3,000 characters (~750 tokens).
     - Add graceful fallback: If an LLM call fails with token limits or rate limits, fall back to template summarization instead of throwing an unhandled HTTP 500 error.

---

## 12. Phase 11: Backend Authentication 401 Resolution, Email-First Beta Flow & Smart Preference Routing

### 12.1 Problem Statement & Objectives
1. **Critical SQLAlchemy ORM Column Comparison Bug in `backend/auth.py`:**
   - In `get_current_user` (`backend/auth.py`), user lookup executes:
     `user = db.query(models.User).filter(str(models.User.id) == user_id).first()`
   - Evaluating `str(models.User.id)` in Python yields `"users.id"`.
   - Python compares `"users.id" == user_id` (UUID string), which evaluates to `False`.
   - SQLAlchemy compiles `filter(False)` to `WHERE 1 = 0` / `WHERE false`, returning `None`.
   - Because `user` is `None`, line 54 immediately executes `raise HTTPException(status_code=401, detail="Could not validate credentials")`.
   - Every single authenticated endpoint (`POST /onboarding/confirm`, `POST /briefing/generate-now`, `GET /me`) rejects valid JWT tokens with HTTP 401 Unauthorized.

2. **Email-First Beta Tester Authentication Flow:**
   - Instead of a hardcoded `beta_tester@startupx.com` account, when a user clicks "Continue as Beta Tester", they enter their email address first.
   - The backend checks if this email already exists and whether the user has already configured their preferences.
   - If the user has already set preferences (e.g., returning user or same user logging in on a different device), the app skips onboarding completely and navigates directly to the main `HomeScreen`.
   - If the user is new or has no preferences, the app routes them to the Preference setup flow (`OnboardingScreen` $\rightarrow$ `PreferenceConfirmationScreen` $\rightarrow$ click "Generate Briefing").

3. **Persistent Beta Login Session (No Re-Login):**
   - Once a beta tester logs in, the session (`access_token`, `user_id`, `has_preferences`) is stored securely in `AsyncStorage`.
   - On subsequent app launches, `AuthContext` automatically restores the authenticated session so the user is never prompted to sign in again.

### 12.2 Required Fixes & Implementation
1. **Fix SQLAlchemy Column Comparison in `backend/auth.py`:**
   - In `get_current_user`: change `filter(str(models.User.id) == user_id)` to `filter(models.User.id == user_id)`.
   - Support `beta_test_access_token` and `beta_` prefixed tokens as a valid fallback bypass.

2. **Add Dedicated Beta Authentication Endpoint (`backend/main.py`):**
   - Create `POST /auth/beta-login`:
     - Request schema: `schemas.BetaLoginRequest` with `email: EmailStr`.
     - Looks up `models.User` by `email == request.email.lower().strip()`.
     - If user does not exist, creates a new `models.User(email=..., timezone="UTC", subscription_status="free")`.
     - Checks if `models.UserPreference` exists for `user.id` $\rightarrow$ `has_preferences: bool`.
     - Generates valid JWT `access_token` using `create_access_token(data={"sub": str(user.id)})`.
     - Returns `{ "access_token": access_token, "user_id": str(user.id), "email": user.email, "has_preferences": has_preferences }`.

3. **Frontend Email-First Modal / Input in `LoginScreen.tsx`:**
   - In `frontend/src/screens/LoginScreen.tsx`:
     - When "Continue as Beta Tester" is pressed, show an email input prompt / dialog asking for their email.
     - Submits to `${API_URL}/auth/beta-login`.
     - Calls `signIn(data.access_token, data.user_id)` and updates `hasPreferences` state.
     - If `data.has_preferences === true`: navigate directly to `'Home'`.
     - If `data.has_preferences === false`: navigate directly to `'Onboarding'`.

4. **Session Persistence in `AuthContext.tsx` & `App.tsx`:**
   - Ensure `AuthContext` initializes with stored token and checks `/me` to restore `hasPreferences` on app start.
   - `RootNavigator` in `App.tsx` dynamically routes authenticated sessions to `Home` if preferences exist, eliminating redundant login prompts on app startup.

---

## 13. Execution Instructions for Antigravity IDE

Antigravity IDE must implement these fixes sequentially by consulting [`fix_progress.md`](file:///home/rohan/Desktop/StartupX/fix_progress.md).
1. Read the instructions for each item in `fix.md`.
2. Apply the code modifications.
3. Run the designated verification command.
4. Mark the task as completed `[x]` in `fix_progress.md`.



