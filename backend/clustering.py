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

def _infer_category(art: Dict[str, Any]) -> str:
    title = (art.get("title") or "").lower()
    source = (art.get("source_name") or art.get("source") or "").lower()
    content = str(art.get("content") or "").lower()
    text = f"{title} {source} {content[:200]}"
    
    if "arxiv" in source or "paper" in text or "benchmark" in text:
        return "AI Research & Methodology"
    if "github" in source or "repo" in text or "framework" in text or "library" in text:
        return "Open Source & Developer Tools"
    if any(k in text for k in ["gpu", "cuda", "hardware", "datacenter", "chip", "nvidia", "tpu", "inference engine", "vllm", "cluster"]):
        return "AI Hardware & Infrastructure"
    if any(k in text for k in ["llm", "gpt", "model", "weights", "diffusion", "reasoning", "multimodal"]):
        return "AI Models & Releases"
    if "security" in text or "cve" in text or "vulnerability" in text:
        return "Security & Privacy"
    return "Tech Strategy & Business"

def _infer_tags(art: Dict[str, Any]) -> List[str]:
    text = f"{art.get('title', '')} {str(art.get('content', ''))[:300]}".lower()
    tags = []
    tag_map = {
        "LLMs": ["llm", "large language model", "gpt", "qwen", "claude", "llama"],
        "AI Infrastructure": ["gpu", "datacenter", "infrastructure", "hardware", "cuda", "accelerator", "vllm"],
        "AI Research": ["arxiv", "preprint", "neural", "attention", "transformer", "diffusion"],
        "Developer Tools": ["github", "developer", "framework", "library", "sdk", "cli"],
        "Open Source": ["open source", "open-source", "apache", "mit license", "weights"],
        "Tech News": ["startup", "venture", "acquisition", "funding"]
    }
    for tag, keywords in tag_map.items():
        if any(k in text for k in keywords):
            tags.append(tag)
    return tags or ["Tech News"]

def cluster_articles(articles: List[Dict[str, Any]], thematic_tags: List[str] = None) -> List[Dict[str, Any]]:
    """
    Cluster articles using local sentence-transformer embeddings to produce 12-25
    topic-coherent, fine-grained story clusters without Groq token limit consumption.
    """
    if not articles:
        return []

    embedder = get_embedder()
    texts = [f"{a.get('title', '')}. {str(a.get('content', ''))[:350]}" for a in articles]
    embeddings = embedder.encode(texts, convert_to_tensor=True)
    cosine_scores = util.cos_sim(embeddings, embeddings)

    similarity_threshold = 0.52
    unassigned = set(range(len(articles)))
    clusters = []

    # 1. Group articles by high semantic similarity (iterative community leader)
    while unassigned:
        best_leader = None
        best_neighbors = []
        for i in unassigned:
            neighbors = [j for j in unassigned if cosine_scores[i][j].item() >= similarity_threshold]
            if len(neighbors) > len(best_neighbors):
                best_leader = i
                best_neighbors = neighbors

        if not best_neighbors or len(best_neighbors) == 1:
            # Remaining items form distinct individual story clusters
            for i in list(unassigned):
                art = articles[i]
                clusters.append({
                    "canonical_title": art.get("title", "Tech Update"),
                    "category": _infer_category(art),
                    "representative_snippet": str(art.get("content", ""))[:200].replace("\n", " ").strip(),
                    "matched_tags": _infer_tags(art),
                    "articles": [art]
                })
            break

        cluster_arts = [articles[idx] for idx in best_neighbors]
        leader_art = articles[best_leader]
        clusters.append({
            "canonical_title": leader_art.get("title", "Tech Development"),
            "category": _infer_category(leader_art),
            "representative_snippet": str(leader_art.get("content", ""))[:200].replace("\n", " ").strip(),
            "matched_tags": _infer_tags(leader_art),
            "articles": cluster_arts
        })
        for idx in best_neighbors:
            unassigned.remove(idx)

    # Sort clusters by number of articles and limit to top 20 most significant
    clusters.sort(key=lambda c: len(c.get("articles", [])), reverse=True)
    final_clusters = clusters[:20]
    logger.info(f"Generated {len(final_clusters)} fine-grained clusters from {len(articles)} articles.")
    return final_clusters

def compute_centroid(canonical_title: str, representative_snippet: str) -> List[float]:
    """
    Computes a 384-dimensional embedding for a cluster using its title and snippet.
    """
    embedder = get_embedder()
    text_to_embed = f"{canonical_title}. {representative_snippet}"
    embedding = embedder.encode(text_to_embed)
    return embedding.tolist()
