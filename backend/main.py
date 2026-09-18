import os
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

import models
import schemas
import pipeline
from db import get_db, engine
from auth import create_access_token, create_refresh_token, get_current_user

# Create tables if not using migrations (for local testing without alembic run yet)
# models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NewsBrief API", version="1.0.0")

from fastapi.staticfiles import StaticFiles
import os
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

# Typically loaded from environment
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "dummy_google_client_id.apps.googleusercontent.com")

from routers.slack_router import slack_router
app.include_router(slack_router)

scheduler = BackgroundScheduler()

def daily_pipeline_job():
    print("Running scheduled daily pipeline...")
    from run_pipeline import run_pipeline
    asyncio.run(run_pipeline())
    print("Scheduled daily pipeline completed.")

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(daily_pipeline_job, 'cron', hour=0, minute=0, timezone='UTC')
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

class GoogleAuthRequest(BaseModel):
    id_token: str

@app.get("/")
def read_root():
    return {"message": "Welcome to NewsBrief API"}

@app.post("/auth/google")
def auth_google(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        # Verify the token with Google
        id_info = id_token.verify_oauth2_token(
            request.id_token, requests.Request(), GOOGLE_CLIENT_ID
        )
        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")
            
    except ValueError:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token",
        )

    # Upsert user
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email,
            created_at=datetime.now(timezone.utc),
            timezone="UTC",
            subscription_status="free"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }

@app.get("/me")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "subscription_status": current_user.subscription_status
    }

@app.post("/auth/sync-premium")
def sync_premium(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.subscription_status = "premium"
    db.commit()
    return {"status": "success", "subscription_status": "premium"}

class PushTokenRequest(BaseModel):
    token: str

@app.post("/users/push-token")
def update_push_token(request: PushTokenRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.expo_push_token = request.token
    db.commit()
    return {"status": "success"}

@app.get("/users/me/email-preferences", response_model=schemas.EmailPreferenceResponse)
def get_email_preferences(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    pref = db.query(models.UserEmailPreference).filter(models.UserEmailPreference.user_id == current_user.id).first()
    if not pref:
        # Return defaults
        return schemas.EmailPreferenceResponse(daily_digest_enabled=True, delivery_time="06:30")
    return schemas.EmailPreferenceResponse(
        daily_digest_enabled=pref.daily_digest_enabled,
        delivery_time=pref.delivery_time
    )

@app.put("/users/me/email-preferences", response_model=schemas.EmailPreferenceResponse)
def update_email_preferences(
    request: schemas.UpdateEmailPreferenceRequest, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    pref = db.query(models.UserEmailPreference).filter(models.UserEmailPreference.user_id == current_user.id).first()
    
    if not pref:
        pref = models.UserEmailPreference(
            user_id=current_user.id,
            daily_digest_enabled=request.daily_digest_enabled if request.daily_digest_enabled is not None else True,
            delivery_time=request.delivery_time if request.delivery_time is not None else "06:30"
        )
        db.add(pref)
    else:
        if request.daily_digest_enabled is not None:
            pref.daily_digest_enabled = request.daily_digest_enabled
        if request.delivery_time is not None:
            pref.delivery_time = request.delivery_time
            
    db.commit()
    db.refresh(pref)
    
    return schemas.EmailPreferenceResponse(
        daily_digest_enabled=pref.daily_digest_enabled,
        delivery_time=pref.delivery_time
    )

def verify_admin_key(key: str = None):
    if key != "mysecret":
        raise HTTPException(status_code=403, detail="Forbidden")
    return True

@app.post("/admin/trigger-pipeline")
def trigger_pipeline(background_tasks: BackgroundTasks, is_admin: bool = Depends(verify_admin_key)):
    from run_pipeline import run_pipeline
    import asyncio
    
    def run_pipeline_sync():
        asyncio.run(run_pipeline())
        
    background_tasks.add_task(run_pipeline_sync)
    return {"status": "Pipeline triggered in background"}

@app.post("/admin/trigger-stage2")
def trigger_stage2(background_tasks: BackgroundTasks, is_admin: bool = Depends(verify_admin_key)):
    from pipeline_stage2 import run_stage2
    
    def run_stage2_sync():
        run_stage2()
        
    background_tasks.add_task(run_stage2_sync)
    return {"status": "Stage 2 Pipeline triggered in background"}

from fastapi.responses import HTMLResponse
import os

@app.get("/admin", response_class=HTMLResponse)
def get_admin_dashboard(is_admin: bool = Depends(verify_admin_key)):
    admin_path = os.path.join(os.path.dirname(__file__), "admin.html")
    with open(admin_path, "r") as f:
        return f.read()

@app.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db), is_admin: bool = Depends(verify_admin_key)):
    total_users = db.query(models.User).count()
    premium_users = db.query(models.User).filter(models.User.subscription_status == "premium").count()
    
    today = datetime.now(timezone.utc).date()
    briefings_today = db.query(models.UserBriefing).filter(models.UserBriefing.batch_date == today).count()
    cards_today = db.query(models.Card).filter(db.func.date(models.Card.generated_at) == today).count()
    
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "briefings_today": briefings_today,
        "cards_today": cards_today
    }

@app.post("/onboarding/extract", response_model=schemas.OnboardingExtractResponse)
def onboarding_extract(
    request: schemas.OnboardingExtractRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # DB-backed Rate Limiting
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    call_count = db.query(models.LLMCallLog).filter(
        models.LLMCallLog.user_id == current_user.id,
        models.LLMCallLog.stage == 'query_extraction',
        models.LLMCallLog.created_at > one_hour_ago
    ).count()
    
    if call_count >= 5:
        raise HTTPException(status_code=429, detail="Too Many Requests")

    try:
        extracted_data = pipeline.extract_preferences_from_paragraph(request.raw_paragraph)
        
        # Log successful call
        log_entry = models.LLMCallLog(
            user_id=current_user.id,
            stage="query_extraction",
            created_at=datetime.now(timezone.utc)
        )
        db.add(log_entry)
        db.commit()
        
        return extracted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.post("/onboarding/confirm")
def onboarding_confirm(
    request: schemas.OnboardingConfirmRequest, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Upsert user preferences
    pref = db.query(models.UserPreference).filter(models.UserPreference.user_id == current_user.id).first()
    
    if pref:
        pref.raw_paragraph = request.raw_paragraph
        pref.search_queries = request.search_queries
        pref.thematic_tags = request.thematic_tags
        pref.tone_bucket = request.tone_bucket
        pref.tone_freeform = request.tone_freeform
        pref.exclude_keywords = request.exclude_keywords
        pref.updated_at = datetime.now(timezone.utc)
    else:
        pref = models.UserPreference(
            user_id=current_user.id,
            raw_paragraph=request.raw_paragraph,
            search_queries=request.search_queries,
            thematic_tags=request.thematic_tags,
            tone_bucket=request.tone_bucket,
            tone_freeform=request.tone_freeform,
            exclude_keywords=request.exclude_keywords,
            updated_at=datetime.now(timezone.utc)
        )
        db.add(pref)
        
    db.commit()
    return {"status": "success", "message": "Preferences saved"}

@app.post("/content/deep-dive", response_model=schemas.DeepDiveResponse)
def get_deep_dive(
    request: schemas.DeepDiveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    import generation
    import ingestion
    
    # 1. Check if Deep Dive already exists
    existing_deep_dive = db.query(models.DeepDive).filter(models.DeepDive.cluster_id == request.cluster_id).first()
    if existing_deep_dive:
        return schemas.DeepDiveResponse(
            cluster_id=str(existing_deep_dive.cluster_id),
            title=existing_deep_dive.title,
            body_markdown=existing_deep_dive.body_markdown
        )
        
    # 2. Fetch the NewsCluster
    cluster = db.query(models.NewsCluster).filter(models.NewsCluster.id == request.cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="News cluster not found")
        
    # 3. Extract full text from URLs
    articles_text = ""
    for idx, ref in enumerate(cluster.article_refs):
        url = ref.get("url")
        if url:
            text = ingestion.extract_article_text(url)
            if text:
                articles_text += f"\n\n--- Source {idx+1}: {ref.get('title')} ---\n{text}"
                
    if not articles_text.strip():
        raise HTTPException(status_code=500, detail="Failed to extract any text for this cluster's articles")
        
    # 4. Generate Deep Dive via LLM
    markdown_content = generation.generate_deep_dive(cluster.canonical_title, articles_text)
    
    # 5. Save and Return
    new_deep_dive = models.DeepDive(
        cluster_id=cluster.id,
        title=f"Deep Dive: {cluster.canonical_title}",
        body_markdown=markdown_content,
        pre_generated=False,
        generated_at=datetime.now(timezone.utc)
    )
    db.add(new_deep_dive)
    db.commit()
    db.refresh(new_deep_dive)
    
    return schemas.DeepDiveResponse(
        cluster_id=str(new_deep_dive.cluster_id),
        title=new_deep_dive.title,
        body_markdown=new_deep_dive.body_markdown
    )

@app.get("/briefing/today", response_model=schemas.BriefingResponse)
def get_briefing_today(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = datetime.now(timezone.utc).date()
    
    # Get the most recent briefing for the user
    latest_briefing = db.query(models.UserBriefing)\
        .filter(models.UserBriefing.user_id == current_user.id)\
        .order_by(models.UserBriefing.batch_date.desc())\
        .first()
        
    if not latest_briefing:
        raise HTTPException(status_code=404, detail="No briefing found. Please ensure you have set your preferences and wait for the next daily batch.")
        
    is_preparing_today = latest_briefing.batch_date != today
    
    # Fetch Super Summary
    super_summary = db.query(models.SuperSummary).filter(models.SuperSummary.id == latest_briefing.super_summary_id).first()
    if not super_summary:
        raise HTTPException(status_code=500, detail="Linked super summary not found")
        
    # Fetch Cards
    cards = db.query(models.Card).filter(models.Card.id.in_(latest_briefing.card_ids)).all()
    
    return schemas.BriefingResponse(
        batch_date=str(latest_briefing.batch_date),
        is_preparing_today=is_preparing_today,
        super_summary=schemas.SuperSummaryResponse(
            id=str(super_summary.id),
            headline=super_summary.headline,
            synthesis=super_summary.synthesis
        ),
        cards=[
            schemas.CardResponse(
                id=str(c.id),
                cluster_id=str(c.cluster_id),
                headline=c.headline,
                bullets=c.bullets,
                source_name=c.source_name,
                source_url=c.source_url
            ) for c in cards
        ]
    )

@app.get("/briefing/today/audio", response_model=schemas.AudioResponse)
def get_briefing_audio(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = datetime.now(timezone.utc).date()
    
    latest_briefing = db.query(models.UserBriefing)\
        .filter(models.UserBriefing.user_id == current_user.id)\
        .order_by(models.UserBriefing.batch_date.desc())\
        .first()
        
    if not latest_briefing:
        raise HTTPException(status_code=404, detail="No briefing found.")
        
    super_summary = db.query(models.SuperSummary).filter(models.SuperSummary.id == latest_briefing.super_summary_id).first()
    if not super_summary:
        raise HTTPException(status_code=404, detail="Super summary not found")
        
    if super_summary.audio_url:
        return schemas.AudioResponse(audio_url=super_summary.audio_url, status="ready")
        
    # Trigger audio generation if not exists
    from services.audio_service import generate_tts_audio
    cards = db.query(models.Card).filter(models.Card.id.in_(latest_briefing.card_ids)).all()
    
    def generate_audio_sync():
        from db import SessionLocal
        db_session = SessionLocal()
        try:
            # Re-fetch in new session
            ss = db_session.query(models.SuperSummary).filter(models.SuperSummary.id == super_summary.id).first()
            cc = db_session.query(models.Card).filter(models.Card.id.in_([c.id for c in cards])).all()
            generate_tts_audio(ss, cc, db_session)
        finally:
            db_session.close()

    background_tasks.add_task(generate_audio_sync)
    return schemas.AudioResponse(audio_url=None, status="generating")

@app.post("/cards/{card_id}/view", response_model=schemas.CardViewResponse)
def view_card(
    card_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    
    # Query views today
    views_today = db.query(models.CardViewLog).filter(
        models.CardViewLog.user_id == current_user.id,
        models.CardViewLog.viewed_at >= start_of_day
    ).count()
    
    if current_user.subscription_status == "free" and views_today >= 5:
        return schemas.CardViewResponse(limit_reached=True, views_today=views_today)
        
    # Log the view
    view_log = models.CardViewLog(
        user_id=current_user.id,
        card_id=card_id,
        viewed_at=datetime.now(timezone.utc)
    )
    db.add(view_log)
    db.commit()
    
    return schemas.CardViewResponse(limit_reached=False, views_today=views_today + 1)
