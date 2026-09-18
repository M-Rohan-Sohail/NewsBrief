import pytest
from unittest.mock import patch, MagicMock
from pipeline_stage2 import run_stage2
from models import UserPreference, NewsCluster, Card

@pytest.fixture
def mock_dependencies():
    with patch("pipeline_stage2.compute_user_embedding") as mock_compute, \
         patch("pipeline_stage2.generate_super_summary") as mock_generate_ss, \
         patch("pipeline_stage2.SessionLocal") as mock_session_cls:
             
        # Mock objects
        mock_compute.return_value = [0.1] * 384
        mock_generate_ss.return_value = {"headline": "Super Headline", "synthesis": "Super Synthesis"}
        
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        
        # We need mock DB objects for queries
        mock_pref = MagicMock(spec=UserPreference)
        mock_pref.user_id = "user123"
        mock_pref.preference_embedding = None
        mock_pref.tone_bucket = "high_signal"
        mock_pref.thematic_tags = ["AI"]
        mock_pref.search_queries = ["Agents"]
        mock_pref.raw_paragraph = "I love AI."
        
        mock_cluster = MagicMock(spec=NewsCluster)
        mock_cluster.id = "cluster123"
        mock_cluster.canonical_title = "Cluster"
        mock_cluster.representative_snippet = "Snippet"
        
        mock_card = MagicMock(spec=Card)
        mock_card.id = "card123"
        
        # Configure the mocked session's query chain
        # The script does multiple queries: UserPreference, NewsCluster, Card, SuperSummary, UserBriefing
        # To make it simple, we can intercept the calls to .all() and .first() based on context
        
        def mock_query(*args, **kwargs):
            query_mock = MagicMock()
            if args[0] == UserPreference:
                query_mock.all.return_value = [mock_pref]
            elif args[0] == NewsCluster:
                # Need to mock filter -> order_by -> limit -> all
                query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_cluster]
            elif args[0] == Card:
                query_mock.filter.return_value.all.return_value = [mock_card]
            else: # SuperSummary or UserBriefing
                query_mock.filter.return_value.first.return_value = None
            return query_mock
            
        mock_session.query.side_effect = mock_query
        
        yield {
            "compute": mock_compute,
            "generate_ss": mock_generate_ss,
            "session": mock_session,
            "pref": mock_pref
        }

def test_run_stage2(mock_dependencies):
    # Execute the pipeline
    run_stage2()
    
    # Check that preference embedding was calculated
    mock_dependencies["compute"].assert_called_once_with(mock_dependencies["pref"])
    
    # Check that generate_super_summary was called once
    mock_dependencies["generate_ss"].assert_called_once()
    
    # Ensure database commit was called at least once (for embedding and final commit)
    assert mock_dependencies["session"].commit.call_count >= 1
    
    # Check that SuperSummary and UserBriefing were added
    add_calls = mock_dependencies["session"].add.call_args_list
    assert len(add_calls) == 2 # 1 SuperSummary, 1 UserBriefing
