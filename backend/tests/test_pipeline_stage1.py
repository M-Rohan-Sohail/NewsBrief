import pytest
from unittest.mock import patch, MagicMock
from pipeline_stage1 import run_stage1
from schemas import RawArticle

@pytest.fixture
def mock_dependencies():
    with patch("pipeline_stage1.fetch_hacker_news") as mock_hn, \
         patch("pipeline_stage1.fetch_github_trending") as mock_gh, \
         patch("pipeline_stage1.fetch_arxiv_papers") as mock_arx, \
         patch("pipeline_stage1.fetch_rss_feeds") as mock_rss, \
         patch("pipeline_stage1.deduplicate_articles") as mock_dedup, \
         patch("pipeline_stage1.cluster_articles") as mock_cluster, \
         patch("pipeline_stage1.compute_centroid") as mock_centroid, \
         patch("pipeline_stage1.pre_generate_base_cards") as mock_cards, \
         patch("pipeline_stage1.pre_generate_deep_dive") as mock_deep_dive, \
         patch("pipeline_stage1.SessionLocal") as mock_session_cls:
             
        # Setup mocks
        mock_hn.return_value = [RawArticle(id="1", title="HN", url="url", source_name="HN", content="content", tags=[])]
        mock_gh.return_value = []
        mock_arx.return_value = []
        mock_rss.return_value = []
        
        mock_dedup.return_value = [{"title": "HN", "content": "content"}]
        mock_cluster.return_value = [{
            "canonical_title": "Cluster 1",
            "category": "Tech",
            "representative_snippet": "Snippet 1",
            "matched_tags": [],
            "articles": [{"title": "HN", "content": "content", "source_name": "HN", "url": "url"}]
        }]
        
        mock_centroid.return_value = [0.1] * 384
        mock_cards.return_value = {
            "high_signal": {"headline": "Card", "bullets": [], "source_name": "src", "source_url": "url"}
        }
        mock_deep_dive.return_value = "# Deep Dive"
        
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        
        yield {
            "hn": mock_hn, "dedup": mock_dedup, "cluster": mock_cluster,
            "centroid": mock_centroid, "cards": mock_cards, "dd": mock_deep_dive,
            "session": mock_session
        }

def test_run_stage1(mock_dependencies):
    # Run the pipeline
    run_stage1()
    
    # Assertions
    mock_dependencies["hn"].assert_called_once()
    mock_dependencies["dedup"].assert_called_once()
    mock_dependencies["cluster"].assert_called_once()
    mock_dependencies["centroid"].assert_called_once_with("Cluster 1", "Snippet 1")
    mock_dependencies["cards"].assert_called_once()
    mock_dependencies["dd"].assert_called_once()
    
    # Ensure database commit was called
    mock_dependencies["session"].commit.assert_called_once()
    
    # Check that NewsCluster, Card, and DeepDive were added
    add_calls = mock_dependencies["session"].add.call_args_list
    assert len(add_calls) == 3 # 1 cluster + 1 card + 1 deep dive
