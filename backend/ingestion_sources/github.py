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
                
                desc = item.get("description") or "Open source software project"
                stars = item.get("stargazers_count", 0)
                forks = item.get("forks_count", 0)
                language = item.get("language") or "Multi-language"
                topics = item.get("topics", []) or []
                topics_str = ", ".join(topics[:6]) if topics else "developer-tools"
                license_name = (item.get("license") or {}).get("spdx_id") or "Open Source"

                # Rich technical summary for LLM summarization and clustering
                content = (
                    f"Repository: {item.get('full_name')}\n"
                    f"Stars: {stars:,} | Forks: {forks:,} | Language: {language} | License: {license_name}\n"
                    f"Topics: {topics_str}\n"
                    f"Overview: {desc}\n"
                    f"URL: {item.get('html_url')}"
                )
                
                tags = ["github", "opensource"]
                if language:
                    tags.append(language.lower())
                tags.extend([t.lower() for t in topics[:4]])
                
                article = RawArticle(
                    id=f"github_{item.get('id')}",
                    title=item.get("full_name", ""),
                    url=item.get("html_url", ""),
                    source_name="GitHub Trending",
                    content=content,
                    published_at=published_at,
                    tags=tags,
                    author=item.get("owner", {}).get("login"),
                    score=stars
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Failed to parse GitHub repo item: {e}")
                
    except Exception as e:
        logger.error(f"Failed to fetch GitHub Trending repositories: {e}")
        
    logger.info(f"Fetched {len(articles)} GitHub repositories.")
    return articles
