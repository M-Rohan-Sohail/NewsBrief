import os
import json
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, util
from groq import Groq

logger = logging.getLogger(__name__)

# Initialize Groq client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Lazy load the SentenceTransformer model to save memory if not needed immediately
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

def deduplicate_articles(articles: List[Dict[str, Any]], threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Filter out near-identical articles based on semantic similarity.
    """
    if not articles:
        return []

    embedder = get_embedder()
    
    # Prepare text for embedding (Title + first ~500 chars of content)
    texts_to_embed = []
    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")
        # Grab roughly the first two paragraphs or ~500 chars
        snippet = content[:500]
        texts_to_embed.append(f"{title}. {snippet}")

    logger.info(f"Computing embeddings for {len(texts_to_embed)} articles...")
    embeddings = embedder.encode(texts_to_embed, convert_to_tensor=True)
    
    # Compute cosine similarities
    cosine_scores = util.cos_sim(embeddings, embeddings)
    
    surviving_indices = set(range(len(articles)))
    
    for i in range(len(articles)):
        if i not in surviving_indices:
            continue
        for j in range(i + 1, len(articles)):
            if j not in surviving_indices:
                continue
            
            # If similarity > threshold, remove the second one
            if cosine_scores[i][j].item() > threshold:
                logger.info(f"Discarding '{articles[j].get('title')}' - highly similar to '{articles[i].get('title')}'")
                surviving_indices.remove(j)
                
    deduped = [articles[i] for i in sorted(list(surviving_indices))]
    logger.info(f"Deduplication complete: {len(articles)} -> {len(deduped)} articles.")
    return deduped

def cluster_articles(articles: List[Dict[str, Any]], thematic_tags: List[str]) -> List[Dict[str, Any]]:
    """
    Group articles into thematic clusters using the Groq LLM.
    """
    if not articles:
        return []

    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Returning a single fallback cluster.")
        return [{
            "canonical_title": "Fallback Cluster",
            "representative_snippet": "Missing API key for clustering.",
            "matched_tags": thematic_tags,
            "articles": articles
        }]

    # Prepare article data for the prompt
    article_summaries = ""
    for idx, article in enumerate(articles):
        title = article.get("title", "")
        snippet = article.get("content", "")[:300].replace("\n", " ")
        article_summaries += f"[{idx}] Title: {title} | Snippet: {snippet}...\n"

    tags_str = ", ".join(thematic_tags)

    prompt = f"""
You are a news editor. Group the following articles into logical thematic clusters based on these tags: {tags_str}.
An article can only belong to ONE cluster. If an article doesn't fit any tag, group it under "Other".

Output MUST be a valid JSON object matching this schema exactly:
{{
  "clusters": [
    {{
      "canonical_title": "A short, overarching title for this cluster",
      "representative_snippet": "A 1-2 sentence synthesis of what this cluster is about",
      "matched_tags": ["tag1", "tag2"],
      "article_indices": [0, 2] // The integer indices of the articles in this cluster
    }}
  ]
}}

Articles:
{article_summaries}
"""

    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        parsed = json.loads(content)
        
        clusters_data = parsed.get("clusters", [])
        
        # Hydrate article indices with actual article objects
        final_clusters = []
        for c in clusters_data:
            cluster_articles = []
            for idx in c.get("article_indices", []):
                if 0 <= idx < len(articles):
                    cluster_articles.append(articles[idx])
            
            c["articles"] = cluster_articles
            del c["article_indices"] # Clean up
            final_clusters.append(c)
            
        return final_clusters
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return []
