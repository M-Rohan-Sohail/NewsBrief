import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.audio_service import generate_tts_audio, generate_audio_script
from models import SuperSummary, Card
from datetime import datetime

@patch("services.audio_service.groq_client")
def test_generate_audio_script(mock_groq_client):
    ss = MagicMock(spec=SuperSummary)
    ss.synthesis = "This is a synthesis."
    
    card = MagicMock(spec=Card)
    card.headline = "Headline"
    card.bullets = ["B1", "B2"]
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock Script from Groq!"
    
    mock_groq_client.chat.completions.create.return_value = mock_response
    
    script = generate_audio_script(ss, [card])
    assert script == "Mock Script from Groq!"
    mock_groq_client.chat.completions.create.assert_called_once()

@patch("services.audio_service.generate_audio_script")
@patch("services.audio_service._synthesize_edge_tts", new_callable=AsyncMock)
def test_generate_tts_audio(mock_synthesize, mock_gen_script):
    mock_gen_script.return_value = "This is the script to read."
    
    ss = MagicMock(spec=SuperSummary)
    ss.id = "mock_uuid"
    ss.batch_date = datetime(2023, 1, 1).date()
    
    mock_db = MagicMock()
    
    url_path = generate_tts_audio(ss, [], mock_db)
    
    assert url_path == "/static/audio/2023-01-01/mock_uuid.mp3"
    mock_synthesize.assert_called_once()
    
    # Assert DB updates
    assert ss.audio_url == "/static/audio/2023-01-01/mock_uuid.mp3"
    assert ss.audio_duration_seconds is not None
    mock_db.commit.assert_called_once()
