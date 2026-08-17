"""
ShadowTrap AI X — Celery Worker Configuration
================================================
Background task queue for CPU-intensive AI analysis,
model training, and report generation.

Usage:
    celery -A celery_worker.celery worker --loglevel=info

Note:
    Celery + Redis is OPTIONAL. If not available, tasks
    run synchronously within the Flask request lifecycle.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

try:
    from celery import Celery
    
    # Configure Celery
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    celery = Celery(
        "shadowtrap",
        broker=redis_url,
        backend=redis_url,
        include=["app.tasks"],
    )
    
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,        # 5-minute hard limit
        task_soft_time_limit=240,   # 4-minute soft limit
        worker_max_tasks_per_child=100,
        worker_prefetch_multiplier=1,
    )
    
    CELERY_AVAILABLE = True
    
except ImportError:
    celery = None
    CELERY_AVAILABLE = False
    print("⚠️  Celery not available — tasks will run synchronously")
