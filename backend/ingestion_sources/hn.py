import httpx
import logging
from typing import List
from schemas import RawArticle
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def fetch_hacker_news() -> List[RawArticle]:
    logger.info("Fetching Hacker News top stories...")
    articles = []
    
    try:
        # Fetch top story IDs
        response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        response.raise_for_status()
        story_ids = response.json()[:60] # Fetch top 60 to filter down
        
        for story_id in story_ids:
            try:
                story_resp = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
                story_resp.raise_for_status()
                item = story_resp.json()
                
                # Check criteria
                if not item or item.get("type") != "story":
                    continue
                if item.get("score", 0) < 30:
                    continue
                if not item.get("url"):
                    continue
                
                published_at = datetime.fromtimestamp(item.get("time", 0), timezone.utc) if item.get("time") else None
                
                article = RawArticle(
                    id=f"hn_{item.get('id')}",
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    source_name="Hacker News",
                    content=item.get("text", item.get("title", "")),
                    published_at=published_at,
                    tags=["hacker-news"],
                    author=item.get("by"),
                    score=item.get("score", 0)
                )
                
                articles.append(article)
                
                if len(articles) >= 30:
                    break
                    
            except Exception as e:
                logger.warning(f"Failed to fetch HN item {story_id}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to fetch Hacker News top stories: {e}")
        
    logger.info(f"Fetched {len(articles)} Hacker News stories.")
    return articles
