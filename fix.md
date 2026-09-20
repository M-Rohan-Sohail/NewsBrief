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

## 7. Execution Instructions for Antigravity IDE


Antigravity IDE must implement these fixes sequentially by consulting [`fix_progress.md`](file:///home/rohan/Desktop/StartupX/fix_progress.md).
1. Read the instructions for each item in `fix.md`.
2. Apply the code modifications.
3. Run the designated verification command.
4. Mark the task as completed `[x]` in `fix_progress.md`.

