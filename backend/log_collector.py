"""
ShadowTrap AI - Log Collector
================================
Standalone process that continuously monitors Cowrie log files
for new entries and automatically processes them.

Usage:
    python log_collector.py
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.services.cowrie_service import parse_cowrie_logs
from app.models.attack import create_attack
from app.models.session import create_session
from app.utils.logger import get_logger

logger = get_logger("log_collector")


class LogCollector:
    """Monitors Cowrie log file and processes new entries."""
    
    def __init__(self, log_path, poll_interval=5):
        self.log_path = log_path
        self.poll_interval = poll_interval
        self.last_size = 0
        self.processed_sessions = set()
    
    def start(self):
        """Start the log collection loop."""
        logger.info(f"📡 Log Collector started. Monitoring: {self.log_path}")
        logger.info(f"Poll interval: {self.poll_interval}s")
        
        # Initialize file position
        if os.path.exists(self.log_path):
            self.last_size = os.path.getsize(self.log_path)
        
        while True:
            try:
                self._check_for_updates()
            except KeyboardInterrupt:
                logger.info("Log Collector stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
            
            time.sleep(self.poll_interval)
    
    def _check_for_updates(self):
        """Check if log file has new content."""
        if not os.path.exists(self.log_path):
            return
        
        current_size = os.path.getsize(self.log_path)
        
        if current_size > self.last_size:
            logger.info(f"New data detected ({current_size - self.last_size} bytes)")
            self._process_logs()
            self.last_size = current_size
    
    def _process_logs(self):
        """Parse and process new log entries."""
        sessions = parse_cowrie_logs(self.log_path)
        
        new_count = 0
        for session in sessions:
            sid = session.get("session_id", "")
            if sid not in self.processed_sessions:
                create_attack(session)
                create_session(session)
                self.processed_sessions.add(sid)
                new_count += 1
                logger.info(f"New session: {sid} from {session.get('src_ip', 'unknown')}")
        
        if new_count > 0:
            logger.info(f"Processed {new_count} new sessions")


if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        log_path = os.getenv("COWRIE_LOG_PATH", "./app/data/sample_cowrie_logs.json")
        collector = LogCollector(log_path)
        collector.start()
