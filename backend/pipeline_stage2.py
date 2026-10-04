import logging
from datetime import date, datetime, timezone
import uuid

from sqlalchemy import asc

from db import SessionLocal
from models import UserPreference, NewsCluster, Card, SuperSummary, UserBriefing
from clustering import get_embedder
from generation import generate_super_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_user_embedding(pref: UserPreference) -> list[float]:
    """
    Computes a 384-dimensional embedding for a user preference.
    """
    embedder = get_embedder()
    tags = " ".join(pref.thematic_tags or [])
    queries = " ".join(pref.search_queries or [])
    text_to_embed = f"{pref.raw_paragraph} {tags} {queries}"
    
    embedding = embedder.encode(text_to_embed)
    return embedding.tolist()

def run_stage2():
    logger.info("=== Starting Stage 2: User Matching & Personalization ===")
    today = date.today()
    now = datetime.now(timezone.utc)
    
    db = SessionLocal()
    try:
        # Get all users who need matching (in practice, this would be chunked)
        user_prefs = db.query(UserPreference).all()
        logger.info(f"Processing personalization for {len(user_prefs)} users.")
        
        for pref in user_prefs:
            user_id = pref.user_id
            
            # 1. Update Preference Embedding if missing
            if pref.preference_embedding is None:
                logger.info(f"Computing preference embedding for user {user_id}")
                pref.preference_embedding = compute_user_embedding(pref)
                db.commit() # Save the embedding
            
            # 2. pgvector: Fetch High-Relevancy clusters for today matching this user
            logger.info(f"Finding top high-relevancy clusters for user {user_id}")
            cluster_results = db.query(
                NewsCluster,
                NewsCluster.embedding.cosine_distance(pref.preference_embedding).label("dist")
            ).filter(
                NewsCluster.batch_date == today,
                NewsCluster.embedding.isnot(None)
            ).order_by("dist").all()
            
            matched_clusters = []
            for c, dist in cluster_results:
                if pref.exclude_keywords:
                    text_blob = f"{c.canonical_title} {c.representative_snippet}".lower()
                    if any(kw.lower() in text_blob for kw in pref.exclude_keywords):
                        continue
                        
                # Enforce strict high relevancy (distance <= 0.65)
                if dist <= 0.65:
                    matched_clusters.append(c)
                elif not matched_clusters:
                    # Guarantee at least 1 cluster if no stories pass strict threshold
                    matched_clusters.append(c)
                    
                if len(matched_clusters) >= 6:
                    break
            
            if not matched_clusters:
                logger.warning(f"No clusters found for today. Skipping user {user_id}.")
                continue
                
            # 3. Fetch corresponding Cards in the user's tone_bucket
            cluster_ids = [c.id for c in matched_clusters]
            effective_tone = pref.tone_bucket if pref.tone_bucket in ["high_signal", "technical_deep", "executive_brief", "casual"] else "high_signal"
            cards = db.query(Card).filter(
                Card.cluster_id.in_(cluster_ids),
                Card.tone_bucket == effective_tone
            ).all()
            if not cards:
                cards = db.query(Card).filter(
                    Card.cluster_id.in_(cluster_ids)
                ).all()
            
            # If a specific tone card doesn't exist, we might fallback to another,
            # but for this MVP, we assume Stage 1 pre-generated all necessary tones.
            card_ids = [c.id for c in cards]
            
            # 4. Generate Super Summary
            # We generate a unique hash/key for this exact combination of clusters
            cluster_set_key = ",".join(sorted([str(c.id) for c in matched_clusters]))
            
            # Check if this exact super summary was already generated today for this tone
            super_summary = db.query(SuperSummary).filter(
                SuperSummary.batch_date == today,
                SuperSummary.cluster_set_key == cluster_set_key,
                SuperSummary.tone_bucket == pref.tone_bucket
            ).first()
            
            if not super_summary:
                logger.info(f"Generating new Super Summary for cluster set {cluster_set_key[:10]}...")
                # We need dicts for generate_super_summary
                cluster_dicts = [
                    {"canonical_title": c.canonical_title, "representative_snippet": c.representative_snippet}
                    for c in matched_clusters
                ]
                
                ss_data = generate_super_summary(cluster_dicts, pref.tone_bucket)
                
                super_summary = SuperSummary(
                    id=uuid.uuid4(),
                    batch_date=today,
                    cluster_set_key=cluster_set_key,
                    tone_bucket=pref.tone_bucket,
                    headline=ss_data.get("headline", "Your Daily Briefing"),
                    synthesis=ss_data.get("synthesis", ""),
                    contributing_cluster_ids=cluster_ids
                )
                db.add(super_summary)
                db.flush() # flush to get the id if needed, though we have it
            
            # 5. Create User Briefing
            logger.info(f"Saving UserBriefing for {user_id}")
            
            # Check if one already exists for today to avoid duplicates
            existing_briefing = db.query(UserBriefing).filter(
                UserBriefing.user_id == user_id,
                UserBriefing.batch_date == today
            ).first()
            
            if existing_briefing:
                existing_briefing.super_summary_id = super_summary.id
                existing_briefing.card_ids = card_ids
            else:
                new_briefing = UserBriefing(
                    user_id=user_id,
                    batch_date=today,
                    super_summary_id=super_summary.id,
                    card_ids=card_ids
                )
                db.add(new_briefing)
                
        db.commit()
        logger.info("=== Stage 2 Pipeline Complete ===")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed during Stage 2 pipeline: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_stage2()
