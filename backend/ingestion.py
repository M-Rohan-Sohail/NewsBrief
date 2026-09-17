import os
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")

def search_news(query: str, limit: int = 3) -> List[Dict[str, str]]:
    """
    Search Google News via Serper.dev API for the given query.
    Restricts results to the past 24 hours ('qdr:d').
    """
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not set. Using mock search results.")
        return [
            {"title": f"Mock News 1 for {query}", "url": "https://example.com/1"},
            {"title": f"Mock News 2 for {query}", "url": "https://example.com/2"}
        ][:limit]

    url = "https://google.serper.dev/news"
    payload = {
        "q": query,
        "tbs": "qdr:d",
        "num": limit
    }
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("news", [])[:limit]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "source": item.get("source", "")
            })
        return results
    except Exception as e:
        logger.error(f"Serper API request failed for query '{query}': {e}")
        return []

def extract_article_text(url: str) -> str:
    """
    Extract readable markdown text from a URL using Jina Reader API.
    """
    jina_url = f"https://r.jina.ai/{url}"
    headers = {}
    if JINA_API_KEY:
        headers["Authorization"] = f"Bearer {JINA_API_KEY}"
        
    try:
        response = requests.get(jina_url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Jina Reader extraction failed for URL '{url}': {e}")
        return ""
