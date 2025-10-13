#!/usr/bin/env python
"""
RQ Worker for background job processing
"""
import os
import sys
import redis
from rq import Worker, Queue, Connection

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings

# Redis connection
redis_conn = redis.from_url(settings.REDIS_URL)

# Define queues
listen = ["scrapers", "cleanup", "default"]


def start_worker():
    """
    Start RQ worker to process jobs from Redis queue.
    """
    print(f"🔧 Starting RQ Worker...")
    print(f"📡 Redis URL: {settings.REDIS_URL}")
    print(f"📋 Listening to queues: {', '.join(listen)}")

    with Connection(redis_conn):
        worker = Worker(list(map(Queue, listen)))
        print(f"✅ Worker started successfully")
        worker.work()


if __name__ == "__main__":
    start_worker()
