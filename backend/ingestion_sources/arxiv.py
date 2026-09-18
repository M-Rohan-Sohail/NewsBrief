import httpx
import logging
import xml.etree.ElementTree as ET
from typing import List
from schemas import RawArticle
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def fetch_arxiv_papers() -> List[RawArticle]:
    logger.info("Fetching arXiv AI/ML preprints...")
    articles = []
    
    try:
        url = "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=30"
        response = httpx.get(url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        for entry in root.findall('atom:entry', ns):
            try:
                # Extract ID
                entry_id = entry.find('atom:id', ns).text
                
                # Extract Title
                title = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
                
                # Extract Summary
                summary = entry.find('atom:summary', ns).text.replace('\n', ' ').strip()
                
                # Extract published date
                published_str = entry.find('atom:published', ns).text
                published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00')) if published_str else datetime.now(timezone.utc)
                
                # Extract authors
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                author_str = ", ".join(authors) if authors else "Unknown"
                
                article = RawArticle(
                    id=f"arxiv_{entry_id.split('/')[-1]}",
                    title=title,
                    url=entry_id,
                    source_name="arXiv",
                    content=summary,
                    published_at=published_at,
                    tags=["arxiv", "ai", "machine-learning"],
                    author=author_str,
                    score=0
                )
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Failed to parse arXiv entry: {e}")
                
    except Exception as e:
        logger.error(f"Failed to fetch arXiv papers: {e}")
        
    logger.info(f"Fetched {len(articles)} arXiv papers.")
    return articles
