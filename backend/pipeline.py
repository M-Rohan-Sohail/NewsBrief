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
You are an expert NLP classifier configuring personalized technical news briefings.
Analyze the user's free-text input and extract granular technical preferences, entities, and negative filters.

EXTRACTION INSTRUCTIONS:
1. Understand technical domains deeply: LLMs, SLMs, GPUs, inference engines (vLLM, SGLang, TensorRT-LLM), fine-tuning (LoRA, QLoRA), synthetic data, RAG, CUDA kernels, model releases, AI agents, and AI infrastructure.
2. If the user mentions "LLM releases and AI infrastructure", generate highly focused search queries and thematic tags targeting these specific technologies.
3. Automatically populate `exclude_keywords` with off-topic noise (e.g. "retail", "e-commerce", "walmart", "celebrity", "sports", "crypto speculation", "politics") unless explicitly requested by the user.
4. Tone Bucket: Set to "technical_deep" or "high_signal".

Output MUST be a valid JSON object matching this schema exactly:
{{
  "search_queries": ["list of 6 to 10 specific search queries targeting exact technical topics"],
  "thematic_tags": ["list of 4 to 8 short thematic tags"],
  "tone_bucket": "one of: technical_deep, high_signal, executive_brief, casual",
  "tone_freeform": "any specific tone instructions from user, or null",
  "exclude_keywords": ["list of off-topic keywords to strictly exclude"]
}}

User Input:
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
                    parsed['tone_bucket'] = 'technical_deep'
                    validated = OnboardingExtractResponse(**parsed)
                else:
                    raise ve
                    
            return validated.model_dump()
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Extraction attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                # Graceful fallback on validation failure
                return {
                    "search_queries": ["LLM model releases", "AI GPU infrastructure", "machine learning benchmarks"],
                    "thematic_tags": ["ai", "llm", "infrastructure"],
                    "tone_bucket": "technical_deep",
                    "tone_freeform": None,
                    "exclude_keywords": ["retail", "celebrity", "e-commerce"]
                }
        except Exception as e:
            logger.warning(f"Extraction API attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                # Graceful fallback on API failure (e.g. rate limit / token limit)
                return {
                    "search_queries": ["LLM model releases", "AI GPU infrastructure", "machine learning benchmarks"],
                    "thematic_tags": ["ai", "llm", "infrastructure"],
                    "tone_bucket": "technical_deep",
                    "tone_freeform": None,
                    "exclude_keywords": ["retail", "celebrity", "e-commerce"]
                }
            
    return {
        "search_queries": ["technology", "business", "science"],
        "thematic_tags": ["tech", "business"],
        "tone_bucket": "high_signal",
        "tone_freeform": None,
        "exclude_keywords": []
    }
