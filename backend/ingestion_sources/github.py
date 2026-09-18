import httpx
import logging
from typing import List
from schemas import RawArticle
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

def fetch_github_trending() -> List[RawArticle]:
    logger.info("Fetching GitHub Trending repositories...")
    articles = []
    
    try:
        # Search for repos active/created in the last 7 days with >100 stars
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        query = f"stars:>100 created:>{seven_days_ago}"
        
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
        
        # We need User-Agent for GitHub API
        headers = {"User-Agent": "NewsBrief-Ingestion-Engine"}
        
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])[:30] # Top 30
        
        for item in items:
            try:
                published_at = datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')) if item.get("created_at") else datetime.now(timezone.utc)
                
                # Use description as content, fallback to name
                content = item.get("description") or item.get("name")
                language = item.get("language")
                tags = ["github", "opensource"]
                if language:
                    tags.append(language.lower())
                
                article = RawArticle(
                    id=f"github_{item.get('id')}",
                    title=item.get("full_name", ""),
                    url=item.get("html_url", ""),
                    source_name="GitHub Trending",
                    content=content,
                    published_at=published_at,
                    tags=tags,
                    author=item.get("owner", {}).get("login"),
                    score=item.get("stargazers_count", 0)
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Failed to parse GitHub repo item: {e}")
                
    except Exception as e:
        logger.error(f"Failed to fetch GitHub Trending repositories: {e}")
        
    logger.info(f"Fetched {len(articles)} GitHub repositories.")
    return articles
