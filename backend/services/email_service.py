import os
import logging
import resend
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from models import User, UserBriefing, SuperSummary, Card

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
# In a real scenario, this is verified and owned by us
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

def build_cards_html(cards: list[Card], app_url: str, user_id: str) -> str:
    """
    Generate the HTML snippet for a list of cards.
    """
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    if api_url.endswith("/"):
        api_url = api_url[:-1]
    
    html = ""
    for card in cards:
        bullets_html = "".join([f"<li>{b}</li>" for b in card.bullets])
        html += f"""
        <div class="card">
            <h3>{card.headline}</h3>
            <ul>
                {bullets_html}
            </ul>
            <div class="card-meta">Source: <a href="{card.source_url}">{card.source_name}</a></div>
            <div class="btn-group">
                <a href="{api_url}/analytics/email-click/{user_id}/{card.cluster_id}" class="btn btn-secondary">Read Deep Dive</a>
            </div>
        </div>
        """
    return html

def send_daily_digest(user_id: str, db: Session, mock_mode: bool = False) -> bool:
    """
    Sends the daily email digest to the user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.email:
        logger.error(f"Cannot send email: User {user_id} not found or missing email")
        return False
        
    today = datetime.now(timezone.utc).date()
    
    # Fetch User Briefing
    briefing = db.query(UserBriefing).filter(
        UserBriefing.user_id == user.id,
        UserBriefing.batch_date == today
    ).first()
    
    if not briefing:
        briefing = db.query(UserBriefing).filter(
            UserBriefing.user_id == user.id
        ).order_by(UserBriefing.batch_date.desc()).first()
        
    if not briefing:
        logger.warning(f"No briefing found for user {user.email}")
        return False
        
    super_summary = db.query(SuperSummary).filter(SuperSummary.id == briefing.super_summary_id).first()
    if not super_summary:
        logger.error(f"Super summary not found for briefing {briefing.user_id}")
        return False
        
    # Get top 3 cards for email (limit to 3 to keep it concise)
    cards = db.query(Card).filter(Card.id.in_(briefing.card_ids)).limit(3).all()
    
    # Load HTML template
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'email_digest.html')
    with open(template_path, 'r') as f:
        html_template = f.read()
        
    app_url = os.environ.get("APP_URL", "http://localhost:3000")
    
    # Replace placeholders
    html_content = html_template.replace("[[DATE]]", today.strftime("%B %d, %Y"))
    html_content = html_content.replace("[[SUPER_HEADLINE]]", super_summary.headline)
    html_content = html_content.replace("[[SUPER_SYNTHESIS]]", super_summary.synthesis)
    html_content = html_content.replace("[[APP_URL]]", app_url)
    
    cards_html = build_cards_html(cards, app_url, str(user.id))
    html_content = html_content.replace("[[CARDS_HTML]]", cards_html)
    
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    if api_url.endswith("/"):
        api_url = api_url[:-1]
        
    pixel_url = f"{api_url}/analytics/email-open/{user.id}/{today}"
    pixel_html = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" />'
    
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", f"{pixel_html}\n</body>")
    else:
        html_content += pixel_html
    
    logger.info(f"Sending email digest to {user.email}...")
    
    if mock_mode or not RESEND_API_KEY:
        logger.info(f"Mock Mode: Skipping actual Resend API call for {user.email}")
        return True
        
    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": user.email,
            "subject": f"NewsBrief Daily: {super_summary.headline}",
            "html": html_content
        })
        logger.info(f"Email sent successfully: {r}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {e}")
        return False
