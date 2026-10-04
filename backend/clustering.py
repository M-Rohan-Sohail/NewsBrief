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

def fallback_clustering(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fallback clustering that groups articles by source and domain into 4 thematic clusters
    if Groq LLM clustering is unavailable or rate-limited.
    Ensures the pipeline NEVER aborts.
    """
    if not articles:
        return []

    buckets = {
        "AI & Machine Learning Breakthroughs": {
            "category": "Artificial Intelligence",
            "representative_snippet": "Latest research preprints, model developments, and machine learning architectures.",
            "matched_tags": ["AI", "Machine Learning", "Research"],
            "articles": []
        },
        "Open Source & Developer Ecosystem": {
            "category": "Software Engineering",
            "representative_snippet": "Trending developer repositories, frameworks, and open source tooling.",
            "matched_tags": ["Developer Tools", "Open Source", "Software"],
            "articles": []
        },
        "Tech Industry & Startup Ecosystem": {
            "category": "Startups & Tech",
            "representative_snippet": "High-signal discussions, venture updates, and product launches across the tech industry.",
            "matched_tags": ["Startups", "Business", "Tech News"],
            "articles": []
        },
        "Global Technology & Policy": {
            "category": "General Tech",
            "representative_snippet": "Global technology updates, digital policy, hardware innovations, and industry shifts.",
            "matched_tags": ["Policy", "Hardware", "World Tech"],
            "articles": []
        }
    }

    for art in articles:
        source = (art.get("source_name") or art.get("source") or "").lower()
        title = (art.get("title") or "").lower()

        if "arxiv" in source or "ai" in source or any(w in title for w in ["llm", "gpt", "model", "neural", "deep learning", "transformer", "diffusion", "rag"]):
            buckets["AI & Machine Learning Breakthroughs"]["articles"].append(art)
        elif "github" in source or any(w in title for w in ["repo", "framework", "library", "sdk", "cli", "compiler"]):
            buckets["Open Source & Developer Ecosystem"]["articles"].append(art)
        elif "hacker news" in source or "hn" in source:
            buckets["Tech Industry & Startup Ecosystem"]["articles"].append(art)
        else:
            buckets["Global Technology & Policy"]["articles"].append(art)

    final_clusters = []
    for title, data in buckets.items():
        if data["articles"]:
            final_clusters.append({
                "canonical_title": title,
                "category": data["category"],
                "representative_snippet": data["representative_snippet"],
                "matched_tags": data["matched_tags"],
                "articles": data["articles"]
            })

    logger.info(f"Fallback clustering grouped {len(articles)} articles into {len(final_clusters)} clusters.")
    return final_clusters

def cluster_articles(articles: List[Dict[str, Any]], thematic_tags: List[str] = None) -> List[Dict[str, Any]]:
    """
    Group articles into thematic clusters using the Groq LLM with a target budget of ~4,800 to 5,000 input tokens.
    Falls back gracefully to domain clustering if Groq rate limits or fails.
    """
    if not articles:
        return []

    if not groq_client:
        logger.warning("GROQ_API_KEY not set. Using domain-based fallback clustering.")
        return fallback_clustering(articles)

    # Balance articles across sources (round-robin) to ensure broad topic diversity
    sources: Dict[str, List[Dict[str, Any]]] = {}
    for art in articles:
        src = art.get("source_name") or art.get("source") or "Web"
        sources.setdefault(src, []).append(art)

    balanced = []
    while len(balanced) < len(articles):
        added = False
        for src in list(sources.keys()):
            if sources[src]:
                balanced.append(sources[src].pop(0))
                added = True
        if not added:
            break

    # Budget target: ~17,500 characters for articles (~4,700 tokens)
    # + ~1,000 char prompt overhead (~250 tokens) = ~4,950 tokens total (leaves 2,050 token buffer below 7,000 limit)
    MAX_CHARS = 17500
    MAX_ARTICLES = 65
    article_summaries = ""
    included_articles = []

    for idx, article in enumerate(balanced):
        title = str(article.get("title", ""))[:80].strip()
        source = str(article.get("source_name") or article.get("source") or "Web")[:20].strip()
        snippet = str(article.get("content", ""))[:180].replace("\n", " ").strip()
        line = f"[{idx}] {title} | Source: {source} | Snippet: {snippet}...\n"

        if len(article_summaries) + len(line) > MAX_CHARS or len(included_articles) >= MAX_ARTICLES:
            break

        article_summaries += line
        included_articles.append(article)

    logger.info(
        f"Clustering {len(included_articles)} articles with context size {len(article_summaries)} chars "
        f"(~{int(len(article_summaries)/3.7)} tokens)..."
    )

    if thematic_tags:
        tags_str = ", ".join(thematic_tags)
        prompt = f"""You are a news editor. Group the following articles into logical thematic clusters based on these tags: {tags_str}.
An article can only belong to ONE cluster. If an article doesn't fit any tag, group it under "Other".
"""
    else:
        prompt = f"""You are a news editor. Group the following articles into logical thematic clusters (e.g., "AI Models", "Open Source", "Security").
Discover the best categories autonomously based on the provided articles.
An article can only belong to ONE cluster.
"""

    prompt += f"""
Output MUST be a valid JSON object matching this schema exactly:
{{
  "clusters": [
    {{
      "canonical_title": "A short, overarching title for this cluster",
      "category": "The overarching broad category this fits into",
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
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        parsed = json.loads(content)
        
        clusters_data = parsed.get("clusters", [])
        
        # Hydrate article indices with actual article objects
        final_clusters = []
        for c in clusters_data:
            cluster_articles_list = []
            for idx in c.get("article_indices", []):
                if 0 <= idx < len(included_articles):
                    cluster_articles_list.append(included_articles[idx])
            
            c["articles"] = cluster_articles_list
            del c["article_indices"] # Clean up
            if cluster_articles_list:
                final_clusters.append(c)
                
        if final_clusters:
            return final_clusters
        else:
            logger.warning("Groq returned empty clusters, using fallback clustering.")
            return fallback_clustering(included_articles or articles)
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}. Activating smart fallback clustering...")
        return fallback_clustering(included_articles or articles)

def compute_centroid(canonical_title: str, representative_snippet: str) -> List[float]:
    """
    Computes a 384-dimensional embedding for a cluster using its title and snippet.
    """
    embedder = get_embedder()
    text_to_embed = f"{canonical_title}. {representative_snippet}"
    embedding = embedder.encode(text_to_embed)
    return embedding.tolist()
