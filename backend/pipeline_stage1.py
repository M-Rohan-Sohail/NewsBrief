import logging
import asyncio
from datetime import date, datetime, timezone
import uuid
import sys

from db import SessionLocal
from models import NewsCluster, Card, DeepDive
from schemas import RawArticle

from ingestion_sources.hn import fetch_hacker_news
from ingestion_sources.github import fetch_github_trending
from ingestion_sources.arxiv import fetch_arxiv_papers
from ingestion_sources.rss import fetch_rss_feeds

from clustering import deduplicate_articles, cluster_articles, compute_centroid
from generation import pre_generate_base_cards, pre_generate_deep_dive

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_stage1():
    logger.info("=== Starting Stage 1: Global World-State Pipeline ===")
    
    # 1. Ingestion
    logger.info("Fetching from all ingestion sources...")
    all_raw_articles = []
    
    try:
        hn_articles = fetch_hacker_news()
        all_raw_articles.extend(hn_articles)
    except Exception as e:
        logger.error(f"Error fetching HN: {e}")
        
    try:
        gh_articles = fetch_github_trending()
        all_raw_articles.extend(gh_articles)
    except Exception as e:
        logger.error(f"Error fetching GitHub: {e}")
        
    try:
        arxiv_articles = fetch_arxiv_papers()
        all_raw_articles.extend(arxiv_articles)
    except Exception as e:
        logger.error(f"Error fetching arXiv: {e}")
        
    try:
        rss_articles = fetch_rss_feeds()
        all_raw_articles.extend(rss_articles)
    except Exception as e:
        logger.error(f"Error fetching RSS: {e}")

    logger.info(f"Total raw articles ingested: {len(all_raw_articles)}")
    
    if not all_raw_articles:
        logger.error("No articles ingested. Aborting Stage 1.")
        return

    # Convert Pydantic models to dicts for clustering functions
    articles_dict = [a.model_dump() for a in all_raw_articles]

    # 2. Deduplication
    logger.info("Deduplicating articles...")
    deduped_articles = deduplicate_articles(articles_dict, threshold=0.82)
    
    # 3. Clustering
    logger.info("Clustering articles...")
    # Batch if necessary, but we will pass them all for now (or up to 100 to avoid context limits)
    # The prompt might fail if it's too large, but Qwen 32k context can handle ~100 articles easily.
    top_articles = deduped_articles[:150] 
    
    clusters = cluster_articles(top_articles)
    logger.info(f"Generated {len(clusters)} canonical clusters.")

    if not clusters:
        logger.error("No clusters generated. Aborting Stage 1.")
        return

    today = date.today()
    now = datetime.now(timezone.utc)

    db = SessionLocal()
    try:
        # Sort clusters by number of articles in them to find "top 10" for Deep Dives
        clusters.sort(key=lambda c: len(c.get("articles", [])), reverse=True)
        
        for idx, cluster_data in enumerate(clusters):
            title = cluster_data.get("canonical_title", "Unknown")
            snippet = cluster_data.get("representative_snippet", "")
            category = cluster_data.get("category", "General Tech")
            matched_tags = cluster_data.get("matched_tags", [])
            articles_in_cluster = cluster_data.get("articles", [])
            
            # 4. Compute Centroid
            logger.info(f"Computing centroid for cluster: {title}")
            embedding = compute_centroid(title, snippet)
            
            # Extract refs
            article_refs = [{"title": a.get("title"), "url": a.get("url"), "source": a.get("source_name")} for a in articles_in_cluster]
            
            cluster_id = uuid.uuid4()
            
            # Create NewsCluster
            db_cluster = NewsCluster(
                id=cluster_id,
                batch_date=today,
                canonical_title=title,
                category=category,
                representative_snippet=snippet,
                source_count=len(articles_in_cluster),
                matched_tags=matched_tags,
                article_refs=article_refs,
                embedding=embedding
            )
            db.add(db_cluster)
            
            # 5. Pre-generate Base Cards
            cards_by_tone = pre_generate_base_cards(cluster_data, ["high_signal", "technical_deep"])
            
            for tone, card_data in cards_by_tone.items():
                db_card = Card(
                    id=uuid.uuid4(),
                    cluster_id=cluster_id,
                    tone_bucket=tone,
                    headline=card_data.get("headline", title),
                    bullets=card_data.get("bullets", []),
                    source_name=card_data.get("source_name", "Unknown"),
                    source_url=card_data.get("source_url", ""),
                    generated_at=now
                )
                db.add(db_card)
                
            # 6. Pre-generate Deep Dive (Top 10 only)
            if idx < 10:
                deep_dive_md = pre_generate_deep_dive(cluster_data)
                db_dd = DeepDive(
                    id=uuid.uuid4(),
                    cluster_id=cluster_id,
                    title=title,
                    body_markdown=deep_dive_md,
                    pre_generated=True,
                    generated_at=now
                )
                db.add(db_dd)
                
        # 7. Commit Transaction
        logger.info("Committing Stage 1 pipeline data to database...")
        db.commit()
        logger.info("=== Stage 1 Pipeline Complete ===")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed during DB upsert: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_stage1()
