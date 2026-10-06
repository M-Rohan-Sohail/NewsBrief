import os
import json
import logging
import re
import html
from typing import Dict, Any, List
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def clean_html_text(text: str) -> str:
    """
    Strips raw HTML tags and unescapes HTML entities from RSS feeds and articles.
    """
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]+>', ' ', text)
    # Unescape HTML entities (&amp;, &nbsp;, &gt;, etc.)
    clean = html.unescape(clean)
    # Collapse multiple whitespaces and trim
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

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
        title = clean_html_text(art.get('title', 'Headline'))
        raw_content = str(art.get('content', ''))[:300]
        snippet = clean_html_text(raw_content)
        context += f"Source {idx+1}: {src} - {title}\n{snippet}...\n"

    cluster_title = clean_html_text(cluster.get('canonical_title', 'Tech Development'))

    prompt = f"""
You are an elite Silicon Valley technical editor specializing in high-density engineering briefings.
Summarize the clustered tech news into a single, high-signal briefing card.

STRICT EDITORIAL RULES:
1. BAN corporate fluff and empty buzzwords (NO "holistic acceleration", "physical backbone", "paradigm shift", "tapestry", "delves", "fosters", "landscape", "revolutionizes").
2. HEADLINE: Active, declarative, and specific. Include exact company/author name, model name, parameter count, or performance delta. Never write generic headlines like "New AI Model Released".
3. BULLETS: Exactly 3 dense, facts-first bullet points. Each bullet MUST start with one of the following exact bold category prefixes:
   • **Core Development:** State the exact product, release, open-weights model, framework, or architectural paper announced.
   • **Technical Architecture & Specs:** Cite concrete technical specifications (e.g. parameter sizes, context window, FP8/INT4 quantization, memory bandwidth, latency, benchmark scores against competitors, or licensing).
   • **Engineering Impact:** Concrete implications for engineers, infrastructure costs, deployment requirements, or migration paths.
4. BAN META BULLETS: NEVER include bullets like "Source: ...", "Source Insight: ...", or meta-attribution lines. Every bullet MUST deliver substantive technical signal.
5. TONE: {tone_bucket} (objective, highly technical, dense signal).

Your output MUST be a valid JSON object matching this schema exactly:
{{
  "headline": "Mistral Releases Codestral 2501 with 256k Context & FIM Support",
  "bullets": [
    "**Core Development:** Mistral AI released Codestral 2501, an updated 22B parameter code completion model optimized for low-latency IDE integration.",
    "**Technical Architecture & Specs:** Benchmarks show 85.2% on HumanEval, supporting 256k token context window with Fill-in-the-Middle (FIM) capabilities under Mistral Non-Production License.",
    "**Engineering Impact:** Cuts inference latency by 35% compared to the previous version and integrates natively into Continue.dev and VS Code extensions."
  ],
  "source_name": "Name of the primary source publication",
  "source_url": "URL of the primary source"
}}

Cluster Title: {cluster_title}
Articles Context:
{context}
"""

    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=350
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to generate card for cluster '{cluster_title}': {e}. Using intelligent fallback.")
        first_art = articles[0] if articles else {}
        snippet = clean_html_text(cluster.get("representative_snippet", ""))
        return {
            "headline": cluster_title,
            "bullets": [
                f"**Core Development:** {snippet if snippet else 'Key technical advancement released today.'}",
                "**Technical Architecture & Specs:** Performance benchmarks, runtime characteristics, and architectural specifications documented in source announcement.",
                "**Engineering Impact:** Production deployment pathways, framework integrations, and developer workflow enhancements provided."
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
        title = clean_html_text(c.get('canonical_title', ''))
        snippet = clean_html_text(str(c.get('representative_snippet', ''))[:150])
        context += f"Story {idx+1}: {title} - {snippet}\n"

    prompt = f"""
You are the Chief Technology Editor synthesizing today's executive briefing.
Write a crisp, high-signal macro synthesis connecting today's top engineering stories into a unified narrative.

STRICT EDITORIAL RULES:
1. BAN generic transitional filler (NO "in an ever-evolving world", "interconnected web", "tapestry of innovation", "physical backbone").
2. HEADLINE: Maximum 8-10 words summarizing the dominant technical theme of the day.
3. SYNTHESIS: Exactly 2 punchy sentences capturing the overarching industry momentum, followed by 3 structured bullet highlights categorized by theme with emojis:
   • ⚡ **[AI Models & Weights]**: 1 dense sentence highlighting model weights, reasoning leaps, or benchmarks.
   • 💻 **[Compute, Chips & Infra]**: 1 dense sentence highlighting GPU clusters, inference engines, memory, or hardware breakthroughs.
   • 🔬 **[Architecture & Open Source]**: 1 dense sentence highlighting open research, algorithmic tricks, or developer frameworks.

Your output MUST be a valid JSON object matching this schema exactly:
{{
  "headline": "A sharp, engaging headline for the day's briefing",
  "synthesis": "Two sentences of overarching synthesis.\\n\\n• ⚡ **[AI Models & Weights]**: ...\\n• 💻 **[Compute, Chips & Infra]**: ...\\n• 🔬 **[Architecture & Open Source]**: ..."
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
            "synthesis": "Today's briefing highlights critical advancements in artificial intelligence models, developer tooling, and compute infrastructure.\n\n• ⚡ **AI Models & Weights**: Breakthroughs in specialized reasoning and open weights releases.\n• 💻 **Compute, Chips & Infra**: New benchmarks in accelerated computing and hardware efficiency.\n• 🔬 **Architecture & Open Source**: Algorithmic optimizations improving real-time inference latency."
        }

def generate_deep_dive(cluster_title: str, articles_text: str) -> str:
    """
    Generate a structured, highly analytical 4-section executive deep dive strictly capped at 800 tokens.
    """
    cluster_title_clean = clean_html_text(cluster_title)
    articles_text_clean = clean_html_text(articles_text)

    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using mock deep dive.")
        return f"# Deep Dive: {cluster_title_clean}\n\n## 1. Executive Summary\nMock context.\n\n## 2. Technical Architecture & Benchmarks\nMock architecture.\n\n## 3. Engineering & Ecosystem Impact\nMock impact.\n\n## 4. Key Takeaways\nMock takeaways."

    prompt = f"""
You are a Principal AI Systems Architect authoring an executive technical deep dive for engineers and technical founders.
Deliver an authoritative, highly analytical breakdown of the subject in standard professional mixed-case English.

STRUCTURE REQUIREMENTS:
Produce exactly 4 structured sections formatted in clean GitHub-style Markdown:

## 1. Executive Summary
State the core announcement, creator/organization, and architectural significance in exactly 2 dense sentences.

## 2. Technical Architecture & Benchmarks
Provide 3 dense, bulleted technical facts (1-2 sentences each) covering:
• Model or system architecture, parameter scale, or algorithmic approach.
• Quantifiable benchmark performance, inference latency, or throughput metrics.
• Hardware requirements, quantization formats, or memory footprint.

## 3. Engineering & Ecosystem Impact
Write 1 focused paragraph (3-4 sentences) analyzing developer workflow changes, production trade-offs, compute economics, and integration constraints compared to current alternatives.

## 4. Key Takeaways
Provide exactly 3 complete, bulleted takeaways for engineering leadership:
• **Architecture Strategy:** Specific deployment or architectural recommendation.
• **Compute & Efficiency:** Key operational or cost insight.
• **Ecosystem Outlook:** Strategic production or tooling takeaway.

STRICT EDITORIAL RULES:
- Write in natural capitalization (NEVER use ALL CAPS).
- BAN generic marketing buzzwords (NO "paradigm shift", "holistic acceleration", "physical backbone", "interconnected web").
- Keep length to ~250 words total so all 4 sections conclude completely within budget.

Topic: {cluster_title_clean}

Source Material:
{articles_text_clean[:2200]}
"""
    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800  # STRICTLY CAPPED to 800 tokens per request as requested
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to generate deep dive: {e}")
        # Clean executive fallback instead of raw error dump
        return f"## 1. Executive Summary\n{cluster_title_clean} represents a notable technical development currently being integrated across source publications.\n\n## 2. Technical Architecture & Benchmarks\n- **Source Ingestion:** Multiple technical reports are analyzing benchmark metrics.\n- **Latency & Compute:** Benchmarks and architectural specifications are being validated.\n\n## 3. Engineering & Ecosystem Impact\nEngineering teams are evaluating deployment feasibility and runtime optimizations.\n\n## 4. Key Takeaways\n- Monitor official repositories for full parameter weights.\n- Review source articles for benchmark replications."

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
        articles_text += f"Title: {clean_html_text(art.get('title', ''))}\n"
        articles_text += f"{clean_html_text(str(art.get('content', ''))[:1000])}\n\n"
        
    logger.info(f"Pre-generating deep dive for '{title}'")
    return generate_deep_dive(title, articles_text)
