from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from db import get_db
from models import UserEventLog, User
from schemas import AnalyticsEventCreate
from auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/event")
def log_event(
    payload: AnalyticsEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = UserEventLog(
        user_id=current_user.id,
        channel=payload.channel,
        event_name=payload.event_name,
        properties=payload.properties
    )
    db.add(event)
    db.commit()
    return {"status": "success"}

@router.get("/email-open/{user_id}/{batch_date}")
def track_email_open(user_id: uuid.UUID, batch_date: str, db: Session = Depends(get_db)):
    # Log the email open event
    event = UserEventLog(
        user_id=user_id,
        channel="email",
        event_name="email_open",
        properties={"batch_date": batch_date}
    )
    db.add(event)
    db.commit()
    
    # Return 1x1 transparent GIF
    gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return Response(content=gif_bytes, media_type="image/gif")

@router.get("/email-click/{user_id}/{cluster_id}")
def track_email_click(
    user_id: uuid.UUID,
    cluster_id: str,
    target: str = "deep-dive",
    db: Session = Depends(get_db)
):
    # Log the email click event
    event = UserEventLog(
        user_id=user_id,
        channel="email",
        event_name="email_click",
        properties={"cluster_id": cluster_id, "target": target}
    )
    db.add(event)
    db.commit()
    
    # Redirect to app deep link or web fallback
    import os
    app_url = os.environ.get("APP_URL", "newsbrief://")
    if app_url.endswith("/"):
        app_url = app_url[:-1]
        
    redirect_url = f"{app_url}/deep-dive/{cluster_id}"
    return RedirectResponse(url=redirect_url, status_code=302)
