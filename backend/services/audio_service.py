import os
import logging
import asyncio
import edge_tts
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from groq import Groq

from models import SuperSummary, Card

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def generate_audio_script(super_summary: SuperSummary, cards: list[Card]) -> str:
    """
    Generates a conversational audio script for the day's briefing using Groq.
    """
    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock audio script.")
        return "Welcome to News Brief! This is a mock audio script because the Groq API key is missing. Enjoy your day!"
        
    cards_text = ""
    for idx, c in enumerate(cards):
        bullets = " ".join(c.bullets)
        cards_text += f"Story {idx+1}: {c.headline}. Details: {bullets}\n"
        
    prompt = f"""
    You are a professional radio host for "NewsBrief Daily". Write a highly conversational, engaging 300-word daily briefing script.
    Read the following overarching summary and key stories, and weave them into a smooth narrative that sounds natural when spoken aloud.
    IMPORTANT: Do not include any formatting, markdown, brackets, sound effect cues, or speaker labels. Just output the raw text that will be fed directly into a Text-to-Speech engine.
    
    Overarching Summary:
    {super_summary.synthesis}
    
    Key Stories:
    {cards_text}
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
        )
        script = response.choices[0].message.content.strip()
        # Clean up any potential markdown that the LLM might have ignored instructions about
        script = script.replace("*", "").replace("#", "").replace("_", "")
        return script
    except Exception as e:
        logger.error(f"Failed to generate audio script: {e}")
        return "Welcome to your NewsBrief daily update. Unfortunately, we experienced an error generating today's script."

async def _synthesize_edge_tts(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_path)
    
def generate_tts_audio(super_summary: SuperSummary, cards: list[Card], db: Session) -> str:
    """
    Generates the audio script, synthesizes it to MP3 using edge-tts, saves to static folder,
    and returns the relative URL to the audio file.
    """
    # 1. Generate Script
    logger.info(f"Generating audio script for SuperSummary {super_summary.id}...")
    script_text = generate_audio_script(super_summary, cards)
    
    # 2. Setup output directory
    date_str = super_summary.batch_date.strftime("%Y-%m-%d")
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'audio', date_str)
    os.makedirs(static_dir, exist_ok=True)
    
    filename = f"{super_summary.id}.mp3"
    filepath = os.path.join(static_dir, filename)
    url_path = f"/static/audio/{date_str}/{filename}"
    
    # 3. Synthesize Audio
    logger.info(f"Synthesizing audio to {filepath}...")
    try:
        # Run async function in synchronous wrapper
        asyncio.run(_synthesize_edge_tts(script_text, filepath))
        
        # 4. Update Database
        super_summary.audio_url = url_path
        # Note: edge-tts doesn't give us duration easily without parsing the MP3,
        # so we'll estimate based on average reading speed of 150 words per minute
        word_count = len(script_text.split())
        estimated_seconds = int((word_count / 150.0) * 60)
        super_summary.audio_duration_seconds = estimated_seconds
        
        db.commit()
        logger.info(f"Successfully generated audio briefing at {url_path}")
        return url_path
    except Exception as e:
        logger.error(f"Failed to synthesize audio using edge-tts: {e}")
        return None
