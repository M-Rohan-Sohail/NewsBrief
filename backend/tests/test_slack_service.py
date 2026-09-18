import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.slack_service import build_briefing_blocks, send_slack_briefing
from models import SuperSummary, Card, SlackInstallation
from routers.slack_router import slack_oauth_callback

def test_build_briefing_blocks():
    ss = MagicMock(spec=SuperSummary)
    ss.headline = "Test Headline"
    ss.batch_date = datetime(2023, 1, 1).date()
    ss.synthesis = "Test synthesis text."
    ss.audio_url = "/static/test.mp3"
    
    card1 = MagicMock(spec=Card)
    card1.headline = "Card 1"
    card1.bullets = ["B1", "B2"]
    card1.source_name = "Source 1"
    card1.source_url = "http://source1.com"
    card1.cluster_id = "cluster1"
    card1.id = "card1"
    
    blocks = build_briefing_blocks(ss, [card1], "http://localhost:3000")
    
    # Header
    assert blocks[0]["type"] == "header"
    assert "Test Headline" in blocks[0]["text"]["text"]
    
    # Synthesis
    assert blocks[1]["type"] == "section"
    assert "Test synthesis text." in blocks[1]["text"]["text"]
    
    # Audio
    assert blocks[3]["type"] == "actions"
    assert blocks[3]["elements"][0]["url"] == "http://localhost:3000/static/test.mp3"
    
    # Card 1
    assert blocks[5]["type"] == "section"
    assert "*Card 1*" in blocks[5]["text"]["text"]
    assert "• B1" in blocks[5]["text"]["text"]
    assert blocks[5]["accessory"]["url"] == "http://localhost:3000/deep-dive/cluster1"

@patch("services.slack_service.WebClient")
def test_send_slack_briefing(mock_webclient_class):
    mock_client = mock_webclient_class.return_value
    mock_client.chat_postMessage.return_value = {"ts": "12345.678"}
    
    installation = MagicMock(spec=SlackInstallation)
    installation.bot_token = "xoxb-test"
    installation.channel_id = "C123"
    
    blocks = [{"type": "divider"}]
    
    result = send_slack_briefing(installation, blocks)
    
    assert result is True
    mock_webclient_class.assert_called_once_with(token="xoxb-test")
    mock_client.chat_postMessage.assert_called_once_with(
        channel="C123",
        blocks=blocks,
        text="Your NewsBrief Daily is here!"
    )

def test_slack_oauth_callback_mocked():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # with SLACK_CLIENT_ID = mock_client_id, it returns success
    response = slack_oauth_callback(code="test_code", state="test", db=mock_db)
    
    assert response["status"] == "Success"
    
    # Team + SlackInstallation should be added
    assert mock_db.add.call_count == 2
    mock_db.commit.assert_called_once()
