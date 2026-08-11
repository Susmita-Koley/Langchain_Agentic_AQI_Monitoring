#!/usr/bin/env python
from __future__ import annotations
from apscheduler.schedulers.blocking import BlockingScheduler
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent.graph import run_agent

logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')
log = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone='Asia/Kolkata')

@scheduler.scheduled_job('cron', hour=8, minute=0, id='aq_daily_run')
def daily_run():
    log.info('Scheduled daily AQ agent run starting...')
    result = run_agent()
    log.info('Daily run complete. Alert: %s', result['alert_level'])

if __name__ == '__main__':
    log.info('Scheduler started. Agent will run daily at 08:00 IST.')
    log.info('Press Ctrl+C to stop.')
    scheduler.start()
