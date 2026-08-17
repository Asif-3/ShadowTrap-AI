"""
ShadowTrap AI - Session Model
===============================
MongoDB operations for tracking attacker sessions.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.extensions import get_db
from app.utils.helpers import serialize_doc, serialize_docs, utc_now
from app.utils.logger import get_logger

logger = get_logger("models.session")


def create_session(session_data):
    """Create or update an attacker session record."""
    db = get_db()
    now = utc_now()
    
    doc = {
        "session_id": session_data.get("session_id", ""),
        "src_ip": session_data.get("src_ip", ""),
        "src_port": session_data.get("src_port", 0),
        "dst_port": session_data.get("dst_port", 22),
        "protocol": session_data.get("protocol", "ssh"),
        "start_time": session_data.get("start_time", now),
        "end_time": session_data.get("end_time", None),
        "duration": session_data.get("duration", 0),
        "command_count": session_data.get("command_count", 0),
        "status": session_data.get("status", "active"),
        "is_live": session_data.get("is_live", False),
        "created_at": now,
        "updated_at": now,
    }
    
    result = db.sessions.update_one(
        {"session_id": doc["session_id"]},
        {"$set": doc},
        upsert=True
    )
    
    return doc["session_id"]


def get_session(session_id):
    """Get a session by session ID."""
    db = get_db()
    doc = db.sessions.find_one({"session_id": session_id})
    return serialize_doc(doc) if doc else None


def get_live_sessions():
    """Get all active sessions."""
    db = get_db()
    docs = db.sessions.find({"is_live": True}).sort("start_time", -1)
    return serialize_docs(list(docs))


def end_session(session_id):
    """Mark a session as completed."""
    db = get_db()
    now = utc_now()
    
    session = db.sessions.find_one({"session_id": session_id})
    if session:
        from app.utils.helpers import make_utc_aware
        start_dt = make_utc_aware(session.get("start_time", now))
        duration = max(0, (now - start_dt).total_seconds())
        
        db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "end_time": now,
                "duration": duration,
                "status": "completed",
                "is_live": False,
                "updated_at": now,
            }}
        )


def get_session_count():
    """Get total session count."""
    db = get_db()
    return db.sessions.count_documents({})
