import feedparser
import logging
from typing import List
from schemas import RawArticle
from datetime import datetime, timezone
from time import mktime
import hashlib

logger = logging.getLogger(__name__)

DEFAULT_FEEDS = [
    "https://stratechery.com/feed/",
    "https://www.semianalysis.com/feed",
    "https://www.latent.space/feed",
    "https://blog.samaltman.com/posts.atom",
    "https://bair.berkeley.edu/blog/feed.xml"
]

def fetch_rss_feeds(feed_urls: List[str] = DEFAULT_FEEDS) -> List[RawArticle]:
    logger.info(f"Fetching {len(feed_urls)} RSS feeds...")
    articles = []
    
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            
            source_name = feed.feed.get("title", "Unknown Source")
            
            for entry in feed.entries[:5]:  # Top 5 per feed
                try:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    content = entry.get("summary", "") or entry.get("description", "")
                    
                    # Some RSS feeds include full content in 'content' array
                    if "content" in entry and len(entry.content) > 0:
                        content = entry.content[0].value
                        
                    author = entry.get("author", source_name)
                    
                    published_at = datetime.now(timezone.utc)
                    if "published_parsed" in entry and entry.published_parsed:
                        published_at = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                        
                    # Generate a unique ID if not present
                    entry_id = entry.get("id", hashlib.md5((link or title).encode()).hexdigest())
                    
                    article = RawArticle(
                        id=f"rss_{entry_id}",
                        title=title,
                        url=link,
                        source_name=source_name,
                        content=content, # This might contain HTML, we'll strip or summarize later
                        published_at=published_at,
                        tags=["rss", "tech", "blog"],
                        author=author,
                        score=0
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse entry in feed {url}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to fetch or parse feed {url}: {e}")
            
    logger.info(f"Fetched {len(articles)} RSS articles.")
    return articles
