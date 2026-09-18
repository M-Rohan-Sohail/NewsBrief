import os
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.web import WebClient

from db import get_db
from models import SlackInstallation, Team

logger = logging.getLogger(__name__)

slack_router = APIRouter(prefix="/slack", tags=["Slack"])

SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID", "mock_client_id")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET", "mock_client_secret")
SLACK_SCOPES = ["chat:write", "channels:read", "commands"]

authorize_url_generator = AuthorizeUrlGenerator(
    client_id=SLACK_CLIENT_ID,
    scopes=SLACK_SCOPES,
)

@slack_router.get("/install")
def slack_install():
    # In production, pass team ID or user state in the state parameter
    state = "random_state_string"
    url = authorize_url_generator.generate(state)
    return RedirectResponse(url)

@slack_router.get("/oauth_callback")
def slack_oauth_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")
        
    client = WebClient()
    
    # In a real environment, we would exchange this:
    # try:
    #     response = client.oauth_v2_access(
    #         client_id=SLACK_CLIENT_ID,
    #         client_secret=SLACK_CLIENT_SECRET,
    #         code=code
    #     )
    # except Exception as e:
    #     raise HTTPException(status_code=400, detail="OAuth failure")
    
    # Mocking for local MVP if mock client ID
    if SLACK_CLIENT_ID == "mock_client_id":
        response = {
            "team": {"id": "T_MOCK_WORKSPACE"},
            "access_token": "xoxb-mock-token",
            "incoming_webhook": {"channel_id": "C_MOCK_CHANNEL"}
        }
    else:
        try:
            res = client.oauth_v2_access(
                client_id=SLACK_CLIENT_ID,
                client_secret=SLACK_CLIENT_SECRET,
                code=code
            )
            response = res.data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"OAuth failure: {e}")
        
    workspace_id = response["team"]["id"]
    bot_token = response["access_token"]
    
    # Use incoming webhook channel if provided, else rely on bot being invited
    channel_id = response.get("incoming_webhook", {}).get("channel_id", "general")
    
    # Upsert installation
    installation = db.query(SlackInstallation).filter(SlackInstallation.workspace_id == workspace_id).first()
    
    if installation:
        installation.bot_token = bot_token
        installation.channel_id = channel_id
    else:
        # Create a mock team for this installation
        new_team = Team(name=f"Slack Team {workspace_id}", created_at=datetime.now(timezone.utc))
        db.add(new_team)
        db.flush()
        
        installation = SlackInstallation(
            team_id=new_team.id,
            workspace_id=workspace_id,
            bot_token=bot_token,
            channel_id=channel_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(installation)
        
    db.commit()
    
    return {"status": "Success", "message": "NewsBrief Slack bot installed!"}
