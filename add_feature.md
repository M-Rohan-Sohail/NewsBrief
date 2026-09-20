# NewsBrief: Beta Launch Feature Specification (Feedback & Analytics)

**Target Repository:** `/home/rohan/Desktop/StartupX`  
**Document Purpose:** Complete, zero-assumption engineering specification for 2 mission-critical Beta Launch features:  
1. **Checkpoint 1 (CP-26): Beta Tester Feedback & Community Upvoting Board**  
2. **Checkpoint 2 (CP-27): Multi-Channel Engagement Analytics Engine & Telemetry Dashboard**  
**Companion Tracker:** [`progress_add_feature.md`](file:///home/rohan/Desktop/StartupX/progress_add_feature.md)

---

## 1. Executive Summary & Strategic Rationale

During a private beta or early-access rollout, **rapid feedback loops** and **channel consumption telemetry** dictate product-market fit:
1. **Feedback & Community Upvoting:** Early tech leaders and AI PMs want a frictionless, transparent way to suggest features, report edge cases, and vote on what matters most. Crowdsourced upvoting directly prioritizes the product roadmap and builds early-adopter loyalty.
2. **Multi-Channel Engagement Analytics:** NewsBrief delivers intelligence across 4 distinct modalities (Mobile App, Morning Email Digest, Edge-TTS Audio Podcast, and Slack Drops). Without multi-channel analytics, the team is blind to *where* users actually extract value. Tracking App opens, session length, email opens, audio completions, and Slack clicks reveals the true channel dominance per user cohort.

---

## 2. Checkpoint 1 (CP-26): Beta Tester Feedback & Upvoting Board

### 2.1 Database Models (`backend/models.py`)
Add two relational models to manage feedback posts and prevent duplicate votes:

```python
class FeedbackCategory(str, enum.Enum):
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    BUG = "bug"
    SOURCE = "source"
    GENERAL = "general"

class FeedbackStatus(str, enum.Enum):
    UNDER_REVIEW = "under_review"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"

class BetaFeedback(Base):
    __tablename__ = "beta_feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(String(1000), nullable=False)
    category = Column(String(30), nullable=False, default="feature")
    status = Column(String(30), nullable=False, default="under_review")
    upvotes_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class FeedbackVote(Base):
    __tablename__ = "feedback_votes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("beta_feedbacks.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("user_id", "feedback_id", name="uq_user_feedback_vote"),
    )
```

### 2.2 Pydantic Schemas (`backend/schemas.py`)
```python
class FeedbackCreate(BaseModel):
    title: str
    description: str
    category: str = "feature"

class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    category: str
    status: str
    upvotes_count: int
    has_upvoted: bool = False
    created_at: datetime

class FeedbackStatusUpdate(BaseModel):
    status: str
```

### 2.3 API Endpoints (`backend/routers/feedback_router.py` & mounted in `backend/main.py`)
- `GET /feedback?sort_by=upvotes`:
  - Returns list of feedback posts.
  - Supports `sort_by=upvotes` (default) or `sort_by=recent`.
  - Calculates `has_upvoted = True` if the authenticated user has an entry in `feedback_votes`.
- `POST /feedback`:
  - Accepts `FeedbackCreate`.
  - Creates the post with `upvotes_count = 1`.
  - Automatically inserts a corresponding `FeedbackVote` for the author.
- `POST /feedback/{feedback_id}/vote`:
  - Toggles upvote state. If user already voted, removes the vote and decrements `upvotes_count`. If not voted, inserts vote and increments `upvotes_count`.
  - Returns `{ "upvoted": bool, "upvotes_count": int }`.
- `PATCH /admin/feedback/{feedback_id}/status?key=mysecret`:
  - Allows admin to update status (`under_review` -> `planned` -> `completed` -> `declined`).

### 2.4 Mobile Frontend UI (`frontend/src/components/FeedbackModal.tsx`)
1. **Trigger Access:** Added to [`frontend/src/screens/HomeScreen.tsx`](file:///home/rohan/Desktop/StartupX/frontend/src/screens/HomeScreen.tsx) header alongside Settings (`💡 Feedback` button).
2. **Tab Filtering:** Segmented control for `Top Voted` vs `Recent`.
3. **Card Presentation:**
   - Upvote button with arrow icon `▲` and count. Highlighted when `has_upvoted == true`. Optimistic state update on press.
   - Category pill: `Feature` (blue), `Bug` (red), `Source` (purple), `Improvement` (green).
   - Status badge: `Under Review`, `Planned`, `Completed`.
   - Title and description.
4. **New Submission Form:**
   - Modal bottom sheet with title input, category selector (chips), and multi-line description input.

### 2.5 Admin Feedback Management (`backend/admin.html`)
- Dedicated **Beta Feedback Board** section in admin dashboard.
- Lists feedback sorted by upvotes.
- Allows one-click status dropdown changes (`under_review`, `planned`, `completed`, `declined`) that call `PATCH /admin/feedback/{id}/status`.

### 2.6 Automated Unit Tests (`backend/tests/test_feedback.py`)
- Test submitting feedback (initial count = 1, author upvote recorded).
- Test listing feedback with correct sorting and `has_upvoted` flag.
- Test toggling upvote (increment and decrement).
- Test admin status change authorization.

---

## 3. Checkpoint 2 (CP-27): Multi-Channel Engagement Analytics Engine & Telemetry Dashboard

### 3.1 Database Model (`backend/models.py`)
Add a unified high-throughput event logging table:

```python
class UserEventLog(Base):
    __tablename__ = "user_event_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    channel = Column(String(30), nullable=False, index=True) # "app", "email", "audio", "slack"
    event_name = Column(String(50), nullable=False, index=True) # "app_open", "app_session", "email_open", "email_click", "audio_play", "slack_click"
    properties = Column(JSON, nullable=True) # {"session_seconds": 185, "cluster_id": "...", "batch_date": "..."}
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
```

### 3.2 Telemetry Ingestion Endpoints (`backend/routers/analytics_router.py`)
1. **Mobile App Telemetry:**
   - `POST /analytics/event`:
     - Body: `{ "channel": "app", "event_name": "app_session", "properties": { "session_seconds": 240 } }`
     - Authenticated via Bearer token.
2. **Email Open Tracking Pixel:**
   - `GET /analytics/email-open/{user_id}/{batch_date}`:
     - Returns a 1x1 transparent GIF (`b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'`).
     - Logs event: `channel="email"`, `event_name="email_open"`, `properties={"batch_date": batch_date}`.
3. **Email Link Click Redirect:**
   - `GET /analytics/email-click/{user_id}/{cluster_id}?target=deep-dive`:
     - Logs event: `channel="email"`, `event_name="email_click"`, `properties={"cluster_id": cluster_id}`.
     - HTTP 302 Redirects to `{APP_URL}/deep-dive/{cluster_id}`.
4. **Audio Briefing Telemetry:**
   - Tracked via `POST /analytics/event` when user initiates audio in `AudioPlayer.tsx` (`event_name="audio_play"`) or finishes (`event_name="audio_complete"`).
5. **Slack Action Tracking:**
   - Handled directly in `backend/routers/slack_router.py` when block actions are received (`event_name="slack_click"`).

### 3.3 Analytics Aggregation Endpoint (`GET /admin/analytics?key=mysecret`)
Returns a complete multi-channel telemetry object:
```json
{
  "total_users": 48,
  "active_users_today": 34,
  "dau_percentage": 70.8,
  "avg_session_seconds": 215,
  "channel_breakdown": {
    "app": { "users_count": 28, "percentage": 58.3, "total_events": 142 },
    "email": { "users_count": 36, "percentage": 75.0, "total_events": 52 },
    "audio": { "users_count": 16, "percentage": 33.3, "total_events": 24 },
    "slack": { "users_count": 10, "percentage": 20.8, "total_events": 18 }
  },
  "channel_dominance_summary": {
    "app_primary": 12,
    "email_primary": 20,
    "audio_primary": 8,
    "slack_primary": 8
  },
  "recent_activity": [
    { "user_email": "user@example.com", "channel": "email", "event_name": "email_open", "time": "2026-09-20T08:15:00Z" }
  ]
}
```

### 3.4 Mobile Client Telemetry Hook (`frontend/src/services/analytics.ts`)
1. Implement `useAppAnalyticsSession()` in `frontend/src/context/AuthContext.tsx` or `App.tsx`:
   - Listens to `AppState.addEventListener('change')`.
   - Records timestamp on `active`.
   - When transitioning to `background` or `inactive`, calculates elapsed seconds and dispatches `POST /analytics/event` with `app_session`.
2. Connect `AudioPlayer.tsx` to emit `audio_play` and `audio_complete`.

### 3.5 Delivery Services Updates
1. **Email Service (`backend/services/email_service.py`):**
   - Inject tracking pixel at the bottom of the email HTML:
     ```html
     <img src="{API_URL}/analytics/email-open/{user.id}/{today}" width="1" height="1" style="display:none;" />
     ```
   - Wrap deep dive buttons with `{API_URL}/analytics/email-click/{user.id}/{card.cluster_id}`.
2. **Slack Router (`backend/routers/slack_router.py`):**
   - Log `slack_click` event when user clicks briefing actions in Slack.

### 3.6 Admin Analytics UI Tab (`backend/admin.html`)
- Integrate an **Analytics Tab** into the existing modern Tailwind dashboard:
  - **Funnel & DAU Cards:** Total Testers, Active Today, Avg Session Time, Overall Conversion.
  - **Visual Channel Dominance Bar Charts:** Progress bars displaying % engagement for App, Email, Audio, and Slack.
  - **Primary Preference Matrix:** Quick breakdown of user distribution by preferred medium.
  - **Real-time Live Activity Feed:** Last 20 actions across all channels.

### 3.7 Automated Unit Tests (`backend/tests/test_analytics.py`)
- Test event logging endpoint (`POST /analytics/event`).
- Test email open tracking pixel returns valid image bytes and logs event.
- Test email click redirect issues 302 and logs event.
- Test analytics aggregation query logic for correct percentages.

---

## 4. Architectural Verification Plan

1. **Database Schema:** Verify Alembic migration creates `beta_feedbacks`, `feedback_votes`, and `user_event_logs` with all indexes and foreign keys.
2. **Unit Tests:**
   - `pytest backend/tests/test_feedback.py`
   - `pytest backend/tests/test_analytics.py`
3. **End-to-End Flow:**
   - Log in on mobile $\rightarrow$ Submit a feedback post $\rightarrow$ Verify it displays in app and `/admin`.
   - Upvote feedback with another test account $\rightarrow$ Verify sorting shifts upvoted item to top.
   - Open app, trigger audio, trigger test email $\rightarrow$ Verify `/admin/analytics` updates App, Audio, and Email metrics in real time.
