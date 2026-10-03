from unittest.mock import patch, MagicMock
from clustering import fallback_clustering, cluster_articles
from generation import generate_card, generate_super_summary

def test_fallback_clustering():
    articles = [
        {"title": "Attention Is All You Need", "source_name": "arXiv", "content": "Transformer architecture for sequence modeling.", "url": "https://arxiv.org/abs/1706.03762"},
        {"title": "facebookresearch/llama", "source_name": "GitHub Trending", "content": "Inference code for LLaMA models.", "url": "https://github.com/facebookresearch/llama"},
        {"title": "Show HN: My New Startup", "source_name": "Hacker News", "content": "We built a modern collaborative platform.", "url": "https://news.ycombinator.com/item?id=123"},
        {"title": "Tech Industry Regulation", "source_name": "TechCrunch", "content": "New global antitrust developments in tech.", "url": "https://techcrunch.com/article"}
    ]
    
    clusters = fallback_clustering(articles)
    assert len(clusters) == 4
    
    titles = [c["canonical_title"] for c in clusters]
    assert "AI & Machine Learning Breakthroughs" in titles
    assert "Open Source & Developer Ecosystem" in titles
    assert "Tech Industry & Startup Ecosystem" in titles
    assert "Global Technology & Policy" in titles
    
    for c in clusters:
        assert "canonical_title" in c
        assert "representative_snippet" in c
        assert "articles" in c
        assert len(c["articles"]) > 0

def test_cluster_articles_budget_and_round_robin():
    articles = []
    for src in ["Hacker News", "GitHub Trending", "arXiv", "TechCrunch"]:
        for i in range(30):
            articles.append({
                "title": f"Article title {i} about engineering and software design",
                "source_name": src,
                "content": "A detailed technical review describing the system architecture and implications. " * 5,
                "url": f"https://example.com/{src}/{i}"
            })
            
    assert len(articles) == 120
    
    # Mock Groq client
    mock_groq = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content='{"clusters": [{"canonical_title": "AI Highlights", "category": "AI", "representative_snippet": "Summary", "matched_tags": ["AI"], "article_indices": [0, 1]}]}'))
    ]
    mock_groq.chat.completions.create.return_value = mock_completion
    
    with patch("clustering.groq_client", mock_groq):
        clusters = cluster_articles(articles)
        
        # Verify Groq was called
        assert mock_groq.chat.completions.create.called
        call_args = mock_groq.chat.completions.create.call_args[1]
        
        # Ensure model is strictly qwen/qwen3.8-27b
        assert call_args["model"] == "qwen/qwen3.8-27b"
        
        prompt_content = call_args["messages"][0]["content"]
        
        # Context budget must be within ~20,000 chars (~5,000 tokens)
        assert len(prompt_content) <= 20000
        # Check that it balanced ~60 articles and didn't pass all 120
        assert "[0]" in prompt_content
        assert "[50]" in prompt_content
        assert "[100]" not in prompt_content # should be capped well before 100
        
        assert len(clusters) == 1
        assert clusters[0]["canonical_title"] == "AI Highlights"
        assert len(clusters[0]["articles"]) == 2

def test_cluster_articles_fallback_on_rate_limit():
    articles = [
        {"title": "Paper on Diffusion", "source_name": "arXiv", "content": "Latent diffusion models for high resolution image synthesis.", "url": "https://arxiv.org/abs/2112.10752"},
        {"title": "cool-tool/cli", "source_name": "GitHub Trending", "content": "Fast CLI written in Rust.", "url": "https://github.com/cool-tool/cli"}
    ]
    
    mock_groq = MagicMock()
    # Simulate Groq 413 or 429 rate limit exception
    mock_groq.chat.completions.create.side_effect = Exception("Rate limit reached: ITPM 7000 exceeded")
    
    with patch("clustering.groq_client", mock_groq):
        clusters = cluster_articles(articles)
        
        # Must gracefully return fallback clusters instead of []
        assert len(clusters) > 0
        titles = [c["canonical_title"] for c in clusters]
        assert any("AI" in t or "Open Source" in t for t in titles)

def test_generate_card_fallback():
    cluster = {
        "canonical_title": "Quantum Computing Advances",
        "representative_snippet": "New qubit coherence records achieved.",
        "articles": [{"title": "Qubit breakthrough", "source_name": "Nature", "url": "https://nature.com"}]
    }
    
    mock_groq = MagicMock()
    mock_groq.chat.completions.create.side_effect = Exception("Groq Rate Limit")
    
    with patch("generation.groq_client", mock_groq):
        card = generate_card(cluster, "high_signal")
        assert card["headline"] == "Quantum Computing Advances"
        assert "New qubit coherence records achieved." in card["bullets"][0]
        assert card["source_name"] == "Nature"
