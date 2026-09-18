import pytest
from unittest.mock import patch, MagicMock
from services.email_service import send_daily_digest, build_cards_html
from models import User, UserBriefing, SuperSummary, Card

def test_build_cards_html():
    # Setup mock cards
    card1 = MagicMock(spec=Card)
    card1.headline = "Test Headline"
    card1.bullets = ["Bullet 1", "Bullet 2"]
    card1.source_name = "TechCrunch"
    card1.source_url = "https://techcrunch.com"
    card1.cluster_id = "123"
    
    html = build_cards_html([card1], "http://localhost:3000")
    
    assert "Test Headline" in html
    assert "<li>Bullet 1</li>" in html
    assert "TechCrunch" in html
    assert "href=\"https://techcrunch.com\"" in html
    assert "href=\"http://localhost:3000/deep-dive/123\"" in html

@patch("services.email_service.resend.Emails.send")
def test_send_daily_digest_mocked(mock_resend_send):
    mock_db = MagicMock()
    
    # Mock User
    mock_user = MagicMock(spec=User)
    mock_user.id = "user1"
    mock_user.email = "test@example.com"
    
    # Mock Briefing
    mock_briefing = MagicMock(spec=UserBriefing)
    mock_briefing.user_id = "user1"
    mock_briefing.super_summary_id = "ss1"
    mock_briefing.card_ids = ["c1"]
    
    # Mock SuperSummary
    mock_ss = MagicMock(spec=SuperSummary)
    mock_ss.headline = "Super Headline"
    mock_ss.synthesis = "Super Synthesis"
    
    # Mock Card
    mock_card = MagicMock(spec=Card)
    mock_card.headline = "Card 1"
    mock_card.bullets = ["B1"]
    mock_card.source_name = "Source"
    mock_card.source_url = "http://example.com"
    mock_card.cluster_id = "cluster1"
    
    # Setup DB Query returns
    def mock_query(*args, **kwargs):
        query_mock = MagicMock()
        if args[0] == User:
            query_mock.filter.return_value.first.return_value = mock_user
        elif args[0] == UserBriefing:
            query_mock.filter.return_value.first.return_value = mock_briefing
        elif args[0] == SuperSummary:
            query_mock.filter.return_value.first.return_value = mock_ss
        elif args[0] == Card:
            query_mock.filter.return_value.limit.return_value.all.return_value = [mock_card]
        return query_mock
        
    mock_db.query.side_effect = mock_query
    
    # Call with mock_mode=False so it hits the actual code block, but since we patched resend it's safe.
    # Actually wait, we set mock_mode=True to skip resend if RESEND_API_KEY is missing.
    # Let's temporarily override RESEND_API_KEY so it tries to call it.
    with patch("services.email_service.RESEND_API_KEY", "dummy_key"):
        result = send_daily_digest("user1", mock_db, mock_mode=False)
        
    assert result is True
    mock_resend_send.assert_called_once()
    
    call_args = mock_resend_send.call_args[0][0]
    assert call_args["to"] == "test@example.com"
    assert "NewsBrief Daily: Super Headline" in call_args["subject"]
    assert "Super Headline" in call_args["html"]
    assert "Super Synthesis" in call_args["html"]
    assert "Card 1" in call_args["html"]
