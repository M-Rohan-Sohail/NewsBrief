import os
import asyncio
from datetime import datetime, timezone
from arq import cron
from arq.connections import RedisSettings
import logging

logger = logging.getLogger(__name__)

async def run_stage1_pipeline_task(ctx):
    logger.info("Worker executing Stage 1 Global Pipeline...")
    import pipeline_stage1
    pipeline_stage1.run_stage1()
    logger.info("Stage 1 completed.")

async def run_stage2_pipeline_task(ctx):
    logger.info("Worker executing Stage 2 Personalization Pipeline...")
    import pipeline_stage2
    pipeline_stage2.run_stage2()
    logger.info("Stage 2 completed.")

async def send_email_digest_task(ctx, user_id: str):
    logger.info(f"Worker sending email digest to user: {user_id}")
    from db import SessionLocal
    from services.email_service import send_daily_digest
    db = SessionLocal()
    try:
        send_daily_digest(user_id, db)
    finally:
        db.close()
    logger.info(f"Email digest sent to {user_id}")

async def post_slack_briefing_task(ctx, team_id: str):
    logger.info(f"Worker posting Slack briefing for team: {team_id}")
    from db import SessionLocal
    from models import SlackInstallation, UserBriefing, SuperSummary, Card
    from services.slack_service import build_briefing_blocks, send_slack_briefing
    db = SessionLocal()
    try:
        inst = db.query(SlackInstallation).filter(SlackInstallation.team_id == team_id).first()
        if inst:
            today = datetime.now(timezone.utc).date()
            briefing = db.query(UserBriefing).filter(UserBriefing.batch_date == today).first()
            if briefing:
                ss = db.query(SuperSummary).filter(SuperSummary.id == briefing.super_summary_id).first()
                cards = db.query(Card).filter(Card.id.in_(briefing.card_ids)).limit(3).all()
                app_url = os.environ.get("APP_URL", "http://localhost:3000")
                blocks = build_briefing_blocks(ss, cards, app_url)
                send_slack_briefing(inst, blocks)
    finally:
        db.close()
    logger.info(f"Slack briefing posted for team: {team_id}")

async def dispatch_hourly_deliveries_task(ctx):
    logger.info("Worker dispatching hourly deliveries...")
    from db import SessionLocal
    from models import UserEmailPreference, SlackInstallation
    db = SessionLocal()
    try:
        # Email deliveries
        prefs = db.query(UserEmailPreference).filter(UserEmailPreference.daily_digest_enabled == True).all()
        for p in prefs:
            try:
                # Trigger email task async
                await ctx['redis'].enqueue_job('send_email_digest_task', str(p.user_id))
            except Exception as e:
                logger.error(f"Failed to enqueue email for {p.user_id}: {e}")
                
        # Slack deliveries
        installations = db.query(SlackInstallation).all()
        for inst in installations:
            try:
                if inst.team_id:
                    await ctx['redis'].enqueue_job('post_slack_briefing_task', str(inst.team_id))
            except Exception as e:
                logger.error(f"Failed to enqueue slack briefing for {inst.team_id}: {e}")
    finally:
        db.close()
    logger.info("Hourly deliveries dispatched.")

class WorkerSettings:
    functions = [
        run_stage1_pipeline_task,
        run_stage2_pipeline_task,
        send_email_digest_task,
        post_slack_briefing_task,
        dispatch_hourly_deliveries_task
    ]
    cron_jobs = [
        cron(run_stage1_pipeline_task, hour=3, minute=0),
        cron(run_stage2_pipeline_task, hour=4, minute=0),
        cron(dispatch_hourly_deliveries_task, minute=0)
    ]
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
