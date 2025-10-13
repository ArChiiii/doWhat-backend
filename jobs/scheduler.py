#!/usr/bin/env python
"""
Simple Cron Scheduler (without rq-scheduler dependency)
This is a basic scheduler that will be replaced with rq-scheduler once we fix compatibility.
"""
import os
import sys
import time
import schedule
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings


def dummy_scraper_job():
    """Placeholder scraper job"""
    print(f"🕷️  Running dummy scraper job at {datetime.utcnow().isoformat()}")
    # TODO: Implement actual scraper job


def dummy_cleanup_job():
    """Placeholder cleanup job"""
    print(f"🧹 Running dummy cleanup job at {datetime.utcnow().isoformat()}")
    # TODO: Implement actual cleanup job


def schedule_jobs():
    """
    Schedule recurring jobs using the 'schedule' library.

    In production, this should be replaced with rq-scheduler for better
    integration with RQ workers.
    """
    print(f"📅 Simple Scheduler started")
    print(f"📡 Environment: {settings.ENVIRONMENT}")
    print(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")

    # Schedule jobs
    schedule.every(6).hours.do(dummy_scraper_job)
    schedule.every().day.at("02:00").do(dummy_cleanup_job)

    print(f"✅ Scheduler configured:")
    print(f"   - Scraper jobs: Every 6 hours")
    print(f"   - Cleanup jobs: Daily at 2:00 AM")

    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    try:
        schedule_jobs()
    except KeyboardInterrupt:
        print(f"\n👋 Scheduler stopped by user")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        sys.exit(1)
