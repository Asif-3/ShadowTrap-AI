"""
ShadowTrap AI - Cowrie Service
=================================
Parses Cowrie honeypot JSON logs and extracts structured
attack session data for storage and analysis.
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from app.utils.logger import get_logger

logger = get_logger("services.cowrie")


def parse_cowrie_logs(log_path):
    """
    Parse Cowrie JSON log file and extract structured sessions.
    
    Cowrie logs are JSON-lines format where each line is a JSON event.
    Events are grouped by session ID to reconstruct attack sessions.
    
    Args:
        log_path: Path to Cowrie JSON log file
        
    Returns:
        List of parsed session dicts ready for database insertion
    """
    if not os.path.exists(log_path):
        logger.error(f"Cowrie log file not found: {log_path}")
        return []
    
    try:
        # Try JSON array format first (sample data)
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith("["):
                events = json.loads(content)
            else:
                # JSON-lines format (real Cowrie logs)
                events = []
                for line in content.split("\n"):
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        logger.error(f"Error reading Cowrie logs: {e}")
        return []
    
    logger.info(f"Parsed {len(events)} Cowrie events from {log_path}")
    
    # Group events by session ID
    sessions = defaultdict(list)
    for event in events:
        session_id = event.get("session", "unknown")
        sessions[session_id].append(event)
    
    # Process each session
    parsed_sessions = []
    for session_id, session_events in sessions.items():
        parsed = _process_session(session_id, session_events)
        if parsed:
            parsed_sessions.append(parsed)
    
    logger.info(f"Extracted {len(parsed_sessions)} attack sessions")
    return parsed_sessions


def _process_session(session_id, events):
    """
    Process a group of Cowrie events into a structured session.
    
    Args:
        session_id: Cowrie session identifier
        events: List of events belonging to this session
        
    Returns:
        Structured session dict or None if invalid
    """
    # Sort events by timestamp
    events.sort(key=lambda e: e.get("timestamp", ""))
    
    session = {
        "session_id": session_id,
        "src_ip": "",
        "src_port": 0,
        "dst_port": 22,
        "protocol": "ssh",
        "username": "",
        "password": "",
        "commands": [],
        "timestamps": [],
        "downloaded_files": [],
        "executed_files": [],
        "login_attempts": [],
        "start_time": None,
        "end_time": None,
        "duration": 0,
        "status": "completed",
        "is_live": False,
    }
    
    for event in events:
        event_id = event.get("eventid", "")
        timestamp = event.get("timestamp", "")
        
        # Extract IP from any event
        if event.get("src_ip") and not session["src_ip"]:
            session["src_ip"] = event["src_ip"]
        
        if event.get("src_port") and not session["src_port"]:
            session["src_port"] = event["src_port"]
        
        if event.get("dst_port"):
            session["dst_port"] = event["dst_port"]
        
        if event.get("protocol"):
            session["protocol"] = event["protocol"]
        
        # Connection events
        if event_id == "cowrie.session.connect":
            session["start_time"] = _parse_timestamp(timestamp)
        
        # Login events
        elif event_id in ("cowrie.login.success", "cowrie.login.failed"):
            attempt = {
                "username": event.get("username", ""),
                "password": event.get("password", ""),
                "success": event_id == "cowrie.login.success",
                "timestamp": timestamp,
            }
            session["login_attempts"].append(attempt)
            
            if event_id == "cowrie.login.success":
                session["username"] = event.get("username", "")
                session["password"] = event.get("password", "")
        
        # Command events
        elif event_id == "cowrie.command.input":
            cmd = event.get("input", "")
            if cmd:
                session["commands"].append(cmd)
                session["timestamps"].append(timestamp)
        
        # File download events
        elif event_id == "cowrie.session.file_download":
            download = {
                "url": event.get("url", ""),
                "outfile": event.get("outfile", ""),
                "timestamp": timestamp,
            }
            session["downloaded_files"].append(download)
        
        # Session close events
        elif event_id == "cowrie.session.closed":
            session["end_time"] = _parse_timestamp(timestamp)
            session["duration"] = event.get("duration", 0)
    
    # Set start time from first event if not set
    if not session["start_time"] and events:
        session["start_time"] = _parse_timestamp(events[0].get("timestamp", ""))
    
    # Set end time from last event if not set
    if not session["end_time"] and events:
        session["end_time"] = _parse_timestamp(events[-1].get("timestamp", ""))
    
    # Calculate duration if not provided
    if session["duration"] == 0 and session["start_time"] and session["end_time"]:
        delta = session["end_time"] - session["start_time"]
        session["duration"] = max(0, delta.total_seconds())
    
    # Skip sessions with no meaningful data
    if not session["src_ip"]:
        return None
    
    return session


def _parse_timestamp(ts_str):
    """Parse a timestamp string into a datetime object."""
    if not ts_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse timestamp: {ts_str}")
    return None


def get_session_replay(session_id, attacks_collection):
    """
    Get command replay data for a specific session.
    
    Args:
        session_id: Session identifier
        attacks_collection: MongoDB attacks collection
        
    Returns:
        List of replay steps with commands and timestamps
    """
    attack = attacks_collection.find_one({"session_id": session_id})
    if not attack:
        return []
    
    commands = attack.get("commands", [])
    timestamps = attack.get("timestamps", [])
    
    replay = []
    for i, cmd in enumerate(commands):
        step = {
            "index": i,
            "command": cmd,
            "timestamp": timestamps[i] if i < len(timestamps) else None,
        }
        
        # Calculate delay from previous command
        if i > 0 and i < len(timestamps) and i - 1 < len(timestamps):
            prev_ts = _parse_timestamp(timestamps[i - 1])
            curr_ts = _parse_timestamp(timestamps[i])
            if prev_ts and curr_ts:
                step["delay"] = max(0, (curr_ts - prev_ts).total_seconds())
            else:
                step["delay"] = 2.0  # Default 2 second delay
        else:
            step["delay"] = 0
        
        replay.append(step)
    
    return replay
