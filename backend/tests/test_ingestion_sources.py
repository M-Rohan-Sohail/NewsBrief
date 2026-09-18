import pytest
from ingestion_sources.hn import fetch_hacker_news
from ingestion_sources.github import fetch_github_trending
from ingestion_sources.arxiv import fetch_arxiv_papers
from ingestion_sources.rss import fetch_rss_feeds

def test_hacker_news_ingestion():
    articles = fetch_hacker_news()
    assert len(articles) > 0, "Should fetch at least one article from HN"
    
    first = articles[0]
    assert first.title, "Title should not be empty"
    assert first.url, "URL should not be empty"
    assert first.source_name == "Hacker News"
    assert first.score >= 30, "Score should be >= 30"
    
def test_github_ingestion():
    articles = fetch_github_trending()
    assert len(articles) > 0, "Should fetch at least one repo from GitHub"
    
    first = articles[0]
    assert first.title, "Title should not be empty"
    assert first.url.startswith("https://github.com"), "URL should be a github link"
    assert first.source_name == "GitHub Trending"
    assert first.score >= 100, "Score (stars) should be >= 100"
    
def test_arxiv_ingestion():
    articles = fetch_arxiv_papers()
    assert len(articles) > 0, "Should fetch at least one paper from arXiv"
    
    first = articles[0]
    assert first.title, "Title should not be empty"
    assert first.url, "URL should not be empty"
    assert first.source_name == "arXiv"
    assert "arxiv" in first.tags
    
def test_rss_ingestion():
    # Only test a single known-good feed for faster testing
    articles = fetch_rss_feeds(["https://bair.berkeley.edu/blog/feed.xml"])
    assert len(articles) > 0, "Should fetch at least one RSS entry"
    
    first = articles[0]
    assert first.title, "Title should not be empty"
    assert first.url, "URL should not be empty"
    assert "rss" in first.tags

def test_collective_ingestion():
    hn = fetch_hacker_news()
    gh = fetch_github_trending()
    arx = fetch_arxiv_papers()
    rss = fetch_rss_feeds(["https://bair.berkeley.edu/blog/feed.xml"])
    
    total = len(hn) + len(gh) + len(arx) + len(rss)
    assert total > 60, f"Expected >60 unique articles, got {total}"
