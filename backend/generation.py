import os
import json
import logging
from typing import Dict, Any, List
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def generate_card(cluster: Dict[str, Any], tone_bucket: str) -> Dict[str, Any]:
    """
    Generate a concise news card from a cluster of articles.
    """
    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock card generation.")
        # We assume the first article is the primary source if available
        primary_source = cluster.get("articles", [{}])[0]
        return {
            "headline": f"[{tone_bucket}] {cluster.get('canonical_title', 'Mock Headline')}",
            "bullets": ["Mock bullet 1.", "Mock bullet 2."],
            "source_name": primary_source.get("source", "Mock Source"),
            "source_url": primary_source.get("url", "https://example.com")
        }

    # Prepare context
    articles = cluster.get("articles", [])
    context = ""
    for idx, art in enumerate(articles):
        context += f"Source {idx+1}: {art.get('source')} - {art.get('title')}\n{art.get('content')[:500]}...\n"

    prompt = f"""
You are an expert news editor writing in a '{tone_bucket}' tone.
Summarize the following cluster of news articles into a single, punchy news card.

Your output MUST be a valid JSON object matching this schema exactly:
{{
  "headline": "A catchy, accurate headline",
  "bullets": ["Bullet point 1", "Bullet point 2", "Bullet point 3 (max 4)"],
  "source_name": "Name of the primary source publication",
  "source_url": "URL of the primary source"
}}

Cluster Title: {cluster.get('canonical_title')}
Cluster Articles Context:
{context}
"""

    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to generate card for cluster '{cluster.get('canonical_title')}': {e}")
        return {
            "headline": cluster.get("canonical_title", "Error Generating Headline"),
            "bullets": ["Failed to generate summary."],
            "source_name": "Unknown",
            "source_url": "#"
        }

def generate_super_summary(clusters: List[Dict[str, Any]], tone_bucket: str) -> Dict[str, Any]:
    """
    Generate an overarching synthesis summary for all the day's clusters.
    """
    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock super summary.")
        return {
            "headline": f"Daily Briefing - {tone_bucket}",
            "synthesis": "This is a mock synthesis of your daily news."
        }

    context = ""
    for idx, c in enumerate(clusters):
        context += f"Story {idx+1}: {c.get('canonical_title')} - {c.get('representative_snippet')}\n"

    prompt = f"""
You are an expert news editor writing in a '{tone_bucket}' tone.
Below are the key news stories for today. Write a single overarching 'Super Summary' paragraph (4-6 sentences) that synthesizes these stories and explains why today's news matters as a whole. Do not just list them; weave them into a narrative.

Your output MUST be a valid JSON object matching this schema exactly:
{{
  "headline": "A catchy headline for the whole day's briefing",
  "synthesis": "The synthesis paragraph text"
}}

Today's Stories:
{context}
"""

    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to generate super summary: {e}")
        return {
            "headline": "Daily Briefing Unavailable",
            "synthesis": "Failed to synthesize the daily news."
        }

def generate_deep_dive(cluster_title: str, articles_text: str) -> str:
    """
    Generate a highly analytical, 4-section structured markdown document from article text.
    """
    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock deep dive.")
        return f"# Deep Dive: {cluster_title}\n\n## Context\nMock context.\n\n## Key Stakeholders\nMock stakeholders.\n\n## Financial/Strategic Impact\nMock impact.\n\n## Future Outlook\nMock outlook."

    prompt = f"""
You are an expert research analyst. Read the following raw article texts and write a comprehensive, highly analytical Deep Dive document.

The document MUST be formatted in Markdown and MUST contain exactly these four sections:
# Context
# Key Stakeholders
# Financial/Strategic Impact
# Future Outlook

Do not include any other sections. Be extremely detailed, concise, and professional.

Cluster Topic: {cluster_title}

Raw Articles Text:
{articles_text}
"""
    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to generate deep dive: {e}")
        return f"# Error Generating Deep Dive\n\nPlease try again later. Details: {e}"
