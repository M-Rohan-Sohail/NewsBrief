import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from db import SessionLocal
import models
from ingestion import search_news, extract_article_text
from clustering import deduplicate_articles, cluster_articles
from generation import generate_card, generate_super_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_ingestion_pipeline():
    logger.info("Starting Full Ingestion, Clustering & Generation Pipeline...")
    
    db = SessionLocal()
    try:
        preferences = db.query(models.UserPreference).all()
        logger.info(f"Found {len(preferences)} user preference sets.")
        
        today = datetime.now(timezone.utc).date()

        for pref in preferences:
            user_id_str = str(pref.user_id)
            logger.info(f"Processing user {user_id_str}")
            
            # Skip if already generated today
            existing_briefing = db.query(models.UserBriefing).filter(
                models.UserBriefing.user_id == pref.user_id,
                models.UserBriefing.batch_date == today
            ).first()
            
            if existing_briefing:
                logger.info(f"  Briefing already exists for user {user_id_str} today. Skipping.")
                continue
            
            user_data: Dict[str, Any] = {
                "user_id": user_id_str,
                "thematic_tags": pref.thematic_tags,
                "tone_bucket": pref.tone_bucket,
                "articles": [],
            }
            
            # 1. Ingestion Phase
            for query in pref.search_queries:
                logger.info(f"  Searching for query: '{query}'")
                search_results = search_news(query, limit=3)
                
                for idx, result in enumerate(search_results):
                    url = result.get("url")
                    title = result.get("title")
                    source = result.get("source")
                    
                    if not url:
                        continue
                        
                    logger.info(f"    Extracting URL {idx+1}: {url}")
                    article_text = extract_article_text(url)
                    
                    if article_text:
                        user_data["articles"].append({
                            "query": query,
                            "title": title,
                            "url": url,
                            "source": source,
                            "content": article_text
                        })
                    else:
                        logger.warning(f"    Failed to extract text for {url}")
            
            if not user_data["articles"]:
                logger.warning(f"  No articles extracted for user {user_id_str}. Skipping.")
                continue
            
            # 2. Deduplication Phase
            logger.info(f"  Deduplicating {len(user_data['articles'])} articles...")
            deduped_articles = deduplicate_articles(user_data["articles"], threshold=0.85)
            
            # 3. Clustering Phase
            logger.info(f"  Clustering {len(deduped_articles)} articles via Groq LLM...")
            clusters = cluster_articles(deduped_articles, pref.thematic_tags)
            
            # 4. Generation & Persistence Phase
            logger.info("  Generating cards and saving to database...")
            
            cluster_ids = []
            card_ids = []
            
            for c_data in clusters:
                # Create NewsCluster
                db_cluster = models.NewsCluster(
                    batch_date=today,
                    canonical_title=c_data.get("canonical_title", "Untitled Cluster"),
                    representative_snippet=c_data.get("representative_snippet", ""),
                    source_count=len(c_data.get("articles", [])),
                    matched_tags=c_data.get("matched_tags", []),
                    article_refs=[{"title": a.get("title"), "url": a.get("url"), "source": a.get("source")} for a in c_data.get("articles", [])]
                )
                db.add(db_cluster)
                db.commit()
                db.refresh(db_cluster)
                cluster_ids.append(db_cluster.id)
                
                # Generate Card
                card_data = generate_card(c_data, pref.tone_bucket)
                db_card = models.Card(
                    cluster_id=db_cluster.id,
                    tone_bucket=pref.tone_bucket,
                    headline=card_data.get("headline", ""),
                    bullets=card_data.get("bullets", []),
                    source_name=card_data.get("source_name", ""),
                    source_url=card_data.get("source_url", ""),
                    generated_at=datetime.now(timezone.utc)
                )
                db.add(db_card)
                db.commit()
                db.refresh(db_card)
                card_ids.append(db_card.id)
                
            # Generate Super Summary
            logger.info("  Generating super summary...")
            super_summary_data = generate_super_summary(clusters, pref.tone_bucket)
            
            db_super_summary = models.SuperSummary(
                batch_date=today,
                cluster_set_key="|".join(sorted([str(c) for c in cluster_ids]))[:255],
                tone_bucket=pref.tone_bucket,
                headline=super_summary_data.get("headline", ""),
                synthesis=super_summary_data.get("synthesis", ""),
                contributing_cluster_ids=cluster_ids
            )
            db.add(db_super_summary)
            db.commit()
            db.refresh(db_super_summary)
            
            # Create User Briefing
            db_briefing = models.UserBriefing(
                user_id=pref.user_id,
                batch_date=today,
                super_summary_id=db_super_summary.id,
                card_ids=card_ids
            )
            db.add(db_briefing)
            db.commit()
            
            logger.info(f"  Successfully created briefing for user {user_id_str}")
            
            # Send Push Notification
            user = db.query(models.User).filter(models.User.id == pref.user_id).first()
            if user and user.expo_push_token:
                try:
                    from notifications import send_push_message
                    send_push_message(
                        token=user.expo_push_token,
                        title="Your Daily Briefing is Ready",
                        message=super_summary_data.get("headline", "Check out your personalized news.")
                    )
                    logger.info(f"  Sent push notification to {user_id_str}")
                except Exception as push_err:
                    logger.error(f"  Failed to send push notification to {user_id_str}: {push_err}")
            
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion_pipeline()
