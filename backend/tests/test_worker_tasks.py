import pytest
from unittest.mock import patch, MagicMock

# Import tasks directly
from worker import (
    run_stage1_pipeline_task,
    run_stage2_pipeline_task,
    send_email_digest_task,
    post_slack_briefing_task,
    dispatch_hourly_deliveries_task,
    WorkerSettings
)

@pytest.mark.asyncio
async def test_run_stage1_pipeline_task():
    with patch('pipeline_stage1.run_stage1') as mock_run:
        await run_stage1_pipeline_task({})
        mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_run_stage2_pipeline_task():
    with patch('pipeline_stage2.run_stage2') as mock_run:
        await run_stage2_pipeline_task({})
        mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_send_email_digest_task():
    with patch('db.SessionLocal') as mock_session, \
         patch('services.email_service.send_daily_digest') as mock_send:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        await send_email_digest_task({}, "user-123")
        
        mock_send.assert_called_once_with("user-123", mock_db)
        mock_db.close.assert_called_once()

@pytest.mark.asyncio
async def test_post_slack_briefing_task():
    with patch('db.SessionLocal') as mock_session, \
         patch('services.slack_service.build_briefing_blocks') as mock_build, \
         patch('services.slack_service.send_slack_briefing') as mock_send:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        # Setup mock db to return None for simple test
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        await post_slack_briefing_task({}, "team-123")
        mock_db.close.assert_called_once()

@pytest.mark.asyncio
async def test_dispatch_hourly_deliveries_task():
    with patch('db.SessionLocal') as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        # Empty results for simple test
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.all.return_value = []
        
        ctx = {'redis': MagicMock()}
        await dispatch_hourly_deliveries_task(ctx)
        
        mock_db.close.assert_called_once()
        ctx['redis'].enqueue_job.assert_not_called()

def test_worker_settings_configured():
    assert len(WorkerSettings.functions) == 5
    assert len(WorkerSettings.cron_jobs) == 3
