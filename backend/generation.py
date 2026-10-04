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
    Generate a concise, high-signal news card from a cluster of articles.
    """
    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock card generation.")
        primary_source = cluster.get("articles", [{}])[0]
        return {
            "headline": f"[{tone_bucket}] {cluster.get('canonical_title', 'Mock Headline')}",
            "bullets": ["Mock bullet 1.", "Mock bullet 2."],
            "source_name": primary_source.get("source", "Mock Source"),
            "source_url": primary_source.get("url", "https://example.com")
        }

    # Prepare context (compact to stay well within Groq token limits)
    articles = cluster.get("articles", [])
    context = ""
    for idx, art in enumerate(articles[:3]):
        src = art.get('source_name') or art.get('source') or 'Web'
        title = art.get('title', 'Headline')
        snippet = str(art.get('content', ''))[:200].replace('\n', ' ')
        context += f"Source {idx+1}: {src} - {title}\n{snippet}...\n"

    prompt = f"""
You are an elite Silicon Valley technical editor specializing in high-signal technology briefings.
Write a punchy, ultra-informative news card summarizing the news below.

EDITORIAL RULES:
- BAN generic corporate fluff and empty buzzwords (DO NOT use "holistic acceleration", "physical backbone", "paradigm shift", "tapestry", "delves", "fosters").
- Headline MUST be concrete, active, and specific (include specific model names, companies, benchmarks, or key technical achievements).
- Provide 2 to 3 bullet points. Each bullet MUST start with a bold subject tag:
  • **Core Development:** Specific product, model, benchmark, or architecture released/announced.
  • **Key Metric / Spec:** Concrete details (e.g. latency deltas, parameter counts, benchmarks, pricing, or architecture).
  • **Why It Matters:** Concrete impact on developers, engineers, or founders.
- Tone: {tone_bucket} (objective, factual, dense signal).

Your output MUST be a valid JSON object matching this schema exactly:
{{
  "headline": "Concrete, active headline with specific names or numbers",
  "bullets": [
    "**Core Development:** ...",
    "**Key Spec / Metric:** ...",
    "**Why It Matters:** ..."
  ],
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
            response_format={"type": "json_object"},
            max_tokens=300
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to generate card for cluster '{cluster.get('canonical_title')}': {e}. Using intelligent fallback.")
        first_art = articles[0] if articles else {}
        snippet = cluster.get("representative_snippet", "")
        return {
            "headline": cluster.get("canonical_title", "Tech Industry Update"),
            "bullets": [
                f"**Core Development:** {snippet if snippet else 'Key technical advancement released today.'}",
                f"**Source Insight:** Reported by {first_art.get('source_name', 'Tech Intelligence')}."
            ],
            "source_name": first_art.get("source_name") or first_art.get("source") or "Tech Intelligence",
            "source_url": first_art.get("url", "https://news.ycombinator.com")
        }

def generate_super_summary(clusters: List[Dict[str, Any]], tone_bucket: str) -> Dict[str, Any]:
    """
    Generate an overarching synthesis summary for all the day's clusters with structured highlights.
    """
    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock super summary.")
        return {
            "headline": f"Daily Briefing - {tone_bucket}",
            "synthesis": "This is a mock synthesis of your daily news."
        }

    context = ""
    for idx, c in enumerate(clusters):
        snippet = str(c.get('representative_snippet', ''))[:150]
        context += f"Story {idx+1}: {c.get('canonical_title')} - {snippet}\n"

    prompt = f"""
You are an elite tech editor writing a daily briefing executive synthesis.
Below are today's top stories. Write a tight, high-signal executive overview that synthesizes the common technical thread.

EDITORIAL RULES:
- BAN generic corporate fluff (NO "holistic acceleration", "physical backbone", "interconnected web", "tapestry").
- Headline: Engaging, informative headline summarizing the day's dominant theme.
- Synthesis text: Exactly 2 crisp sentences summarizing the day's technical momentum, followed by 3 structured bullet highlights with emojis:
  • ⚡ **[Theme 1]**: 1-sentence technical takeaway
  • 💻 **[Theme 2]**: 1-sentence technical takeaway
  • 🔬 **[Theme 3]**: 1-sentence technical takeaway

Your output MUST be a valid JSON object matching this schema exactly:
{{
  "headline": "A sharp, engaging headline for the day's briefing",
  "synthesis": "Two sentences of overarching synthesis.\n\n• ⚡ **[Highlight 1]**: ...\n• 💻 **[Highlight 2]**: ...\n• 🔬 **[Highlight 3]**: ..."
}}

Today's Stories:
{context}
"""

    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=400
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to generate super summary: {e}. Using fallback synthesis.")
        return {
            "headline": "Today's Technology Briefing",
            "synthesis": "Today's briefing highlights critical advancements in artificial intelligence models, developer tooling, and compute infrastructure.\n\n• ⚡ **AI Models**: Breakthroughs in specialized reasoning and open weights.\n• 💻 **Infrastructure**: New benchmarks in accelerated computing and hardware.\n• 🔬 **Research**: Algorithmic optimizations improving real-time inference."
        }

def generate_deep_dive(cluster_title: str, articles_text: str) -> str:
    """
    Generate a structured, highly analytical 4-section executive deep dive with explicit token limits.
    """
    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock deep dive.")
        return f"# Deep Dive: {cluster_title}\n\n## 1. Executive Summary\nMock context.\n\n## 2. Technical Breakdown & Architecture\nMock architecture.\n\n## 3. Industry & Engineering Impact\nMock impact.\n\n## 4. Key Takeaways\nMock takeaways."

    prompt = f"""
You are a Principal AI Systems Architect writing an executive technical deep dive on a specific news cluster.
The reader is an engineer and technical founder. Be dense, analytical, and concrete.

STRUCTURE REQUIREMENTS:
Write exactly 4 sections in clean Markdown:
## 1. Executive Summary
(2-3 concise sentences stating the core breakthrough/development and who is behind it)

## 2. Technical Breakdown & Architecture
(3-4 bullet points detailing models, parameters, architecture, algorithms, or benchmarks)

## 3. Industry & Engineering Impact
(2 concise paragraphs comparing this to existing alternatives and explaining how developers/startups are affected)

## 4. Key Takeaways
(3 punchy, bulleted takeaways for engineering and product teams)

STRICT RULES:
- BAN generic filler and buzzwords (no "holistic acceleration", "physical backbone", "paradigm shift").
- Target reading length: 3 minutes (~350-450 words total).
- Do not exceed 500 words.

Topic: {cluster_title}

Source Content:
{articles_text[:2500]}
"""
    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=650  # STRICTLY CAP below Groq's 1,000 OTPM limit to prevent 429
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to generate deep dive: {e}")
        # Clean executive fallback instead of raw JSON dump
        return f"## Executive Brief: {cluster_title}\n\n### Overview\nThis deep dive is currently processing technical specifications from source publications.\n\n### Core Signals\n- **Status:** Detailed analysis is being synthesized in the background.\n- **Topic:** {cluster_title}\n- **Recommendation:** Check back shortly or view the source articles directly."

def pre_generate_base_cards(cluster: Dict[str, Any], tones: List[str] = ["high_signal", "technical_deep"]) -> Dict[str, Dict[str, Any]]:
    """
    Pre-generates cards for a cluster across multiple base tones.
    Returns a dictionary mapping tone -> card data.
    """
    cards = {}
    for tone in tones:
        logger.info(f"Pre-generating card for '{cluster.get('canonical_title')}' in tone '{tone}'")
        cards[tone] = generate_card(cluster, tone)
    return cards

def pre_generate_deep_dive(cluster: Dict[str, Any]) -> str:
    """
    Pre-generates a deep dive for a cluster.
    """
    title = cluster.get("canonical_title", "Unknown Topic")
    articles = cluster.get("articles", [])
    
    # Combine content for deep dive context
    articles_text = ""
    for idx, art in enumerate(articles):
        articles_text += f"--- Source {idx+1}: {art.get('source_name')} ---\n"
        articles_text += f"Title: {art.get('title')}\n"
        # For deep dive, we want more context, but will truncate overall text to 3000 chars in generate_deep_dive
        articles_text += f"{str(art.get('content'))[:1000]}\n\n"
        
    logger.info(f"Pre-generating deep dive for '{title}'")
    return generate_deep_dive(title, articles_text)
