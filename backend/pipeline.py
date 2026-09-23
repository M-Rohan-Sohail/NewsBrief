import os
import json
import logging
from groq import Groq
from pydantic import ValidationError
from schemas import OnboardingExtractResponse

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def extract_preferences_from_paragraph(paragraph: str, retries: int = 1) -> dict:
    if not client:
        raise RuntimeError("GROQ_API_KEY is not set. Cannot run extraction.")
        
    paragraph = paragraph[:1000]

    prompt = f"""
You are an expert content analyzer for a news briefing application.
Extract the user's news interests from the following paragraph.
Output MUST be a valid JSON object matching this schema exactly:
{{
  "search_queries": ["list of 5 to 8 specific google search queries"],
  "thematic_tags": ["list of 4 to 8 short thematic tags"],
  "tone_bucket": "one of: high_signal, technical_deep, casual, executive_brief, default",
  "tone_freeform": "any specific tone instructions from the user, or null",
  "exclude_keywords": ["list of keywords to exclude, or empty array"]
}}

Paragraph:
{paragraph}
"""

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Validate against schema
            try:
                validated = OnboardingExtractResponse(**parsed)
            except ValidationError as ve:
                # If tone bucket is the only error, try to patch it to default
                if any(err.get('loc') == ('tone_bucket',) for err in ve.errors()):
                    parsed['tone_bucket'] = 'high_signal'
                    validated = OnboardingExtractResponse(**parsed)
                else:
                    raise ve
                    
            return validated.model_dump()
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Extraction attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                # Graceful fallback on validation failure
                return {
                    "search_queries": ["technology", "business", "science"],
                    "thematic_tags": ["tech", "business"],
                    "tone_bucket": "high_signal",
                    "tone_freeform": None,
                    "exclude_keywords": []
                }
        except Exception as e:
            logger.warning(f"Extraction API attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                # Graceful fallback on API failure (e.g. rate limit / token limit)
                return {
                    "search_queries": ["technology", "business", "science"],
                    "thematic_tags": ["tech", "business"],
                    "tone_bucket": "high_signal",
                    "tone_freeform": None,
                    "exclude_keywords": []
                }
            
    return {
        "search_queries": ["technology", "business", "science"],
        "thematic_tags": ["tech", "business"],
        "tone_bucket": "high_signal",
        "tone_freeform": None,
        "exclude_keywords": []
    }
