"""
ShadowTrap AI - Attack Model
==============================
MongoDB document schema and operations for attack/session data.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.extensions import get_db
from app.utils.helpers import serialize_doc, serialize_docs, utc_now, paginate_query
from app.utils.logger import get_logger

logger = get_logger("models.attack")


def create_attack(attack_data):
    """
    Insert a new attack record from parsed Cowrie log data.
    
    Args:
        attack_data: Dict containing attack fields
        
    Returns:
        Inserted document ID as string
    """
    db = get_db()
    
    now = utc_now()
    doc = {
        "session_id": attack_data.get("session_id", ""),
        "src_ip": attack_data.get("src_ip", ""),
        "src_port": attack_data.get("src_port", 0),
        "dst_port": attack_data.get("dst_port", 22),
        "protocol": attack_data.get("protocol", "ssh"),
        "username": attack_data.get("username", ""),
        "password": attack_data.get("password", ""),
        "commands": attack_data.get("commands", []),
        "timestamps": attack_data.get("timestamps", []),
        "downloaded_files": attack_data.get("downloaded_files", []),
        "executed_files": attack_data.get("executed_files", []),
        "start_time": attack_data.get("start_time", now),
        "end_time": attack_data.get("end_time", None),
        "duration": attack_data.get("duration", 0),
        "command_count": len(attack_data.get("commands", [])),
        "status": attack_data.get("status", "active"),  # active, completed, analyzing
        "threat_score": attack_data.get("threat_score", 0),
        "attack_stage": attack_data.get("attack_stage", None),
        "intent": attack_data.get("intent", None),
        "persona": attack_data.get("persona", None),
        "is_live": attack_data.get("is_live", False),
        "created_at": now,
        "updated_at": now,
    }
    
    # Upsert by session_id to avoid duplicates
    result = db.attacks.update_one(
        {"session_id": doc["session_id"]},
        {"$set": doc},
        upsert=True
    )
    
    if result.upserted_id:
        logger.info(f"New attack created: session={doc['session_id']} ip={doc['src_ip']}")
        # Telegram notifications are now handled by the copilot service
        # after AI analysis, with threshold filtering. Direct notification
        # is only sent for high-score events via the legacy compatibility path.
        try:
            from app.services.telegram_service import send_telegram_notification
            send_telegram_notification(doc)
        except Exception as e:
            logger.warning(f"Telegram notification skipped: {e}")
        return str(result.upserted_id)
    else:
        logger.debug(f"Attack updated: session={doc['session_id']}")
        existing = db.attacks.find_one({"session_id": doc["session_id"]})
        return str(existing["_id"]) if existing else None


def get_attack_by_id(attack_id):
    """Get a single attack by its ObjectId."""
    db = get_db()
    doc = db.attacks.find_one({"_id": ObjectId(attack_id)})
    if doc:
        sid = doc.get("session_id")
        ai_doc = db.ai_analyses.find_one({"session_id": sid})
        if ai_doc:
            doc["ai_analysis"] = serialize_doc(ai_doc)
        llm_doc = db.llm_summaries.find_one({"session_id": sid})
        if llm_doc:
            doc["llm"] = serialize_doc(llm_doc)
    return serialize_doc(doc) if doc else None


def get_attack_by_session(session_id):
    """Get a single attack by session ID."""
    db = get_db()
    doc = db.attacks.find_one({"session_id": session_id})
    if doc:
        ai_doc = db.ai_analyses.find_one({"session_id": session_id})
        if ai_doc:
            doc["ai_analysis"] = serialize_doc(ai_doc)
        llm_doc = db.llm_summaries.find_one({"session_id": session_id})
        if llm_doc:
            doc["llm"] = serialize_doc(llm_doc)
    return serialize_doc(doc) if doc else None


def get_attacks(page=1, per_page=20, filters=None):
    """
    Get paginated list of attacks with optional filters.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        filters: Dict of query filters
        
    Returns:
        Paginated result dict
    """
    db = get_db()
    query = filters or {}
    return paginate_query(db.attacks, query, page, per_page, "created_at", -1)


def get_live_attacks():
    """Get all currently active/live attack sessions."""
    db = get_db()
    docs = db.attacks.find({"is_live": True}).sort("start_time", -1)
    return serialize_docs(list(docs))


def get_recent_attacks(limit=10):
    """Get most recent attacks."""
    db = get_db()
    docs = db.attacks.find().sort("created_at", -1).limit(limit)
    return serialize_docs(list(docs))


def update_attack(session_id, updates):
    """Update attack fields by session ID."""
    db = get_db()
    updates["updated_at"] = utc_now()
    db.attacks.update_one(
        {"session_id": session_id},
        {"$set": updates}
    )


def delete_attacks(session_ids):
    """Delete multiple attacks by session IDs."""
    db = get_db()
    
    # Also delete associated data
    db.attacks.delete_many({"session_id": {"$in": session_ids}})
    db.llm_summaries.delete_many({"session_id": {"$in": session_ids}})
    db.attack_stages.delete_many({"session_id": {"$in": session_ids}})
    db.intents.delete_many({"session_id": {"$in": session_ids}})
    db.predictions.delete_many({"session_id": {"$in": session_ids}})
    db.personas.delete_many({"session_id": {"$in": session_ids}})
    db.threat_scores.delete_many({"session_id": {"$in": session_ids}})


def get_attack_stats():
    """
    Get aggregate attack statistics for dashboard.
    
    Returns:
        Dict with total_attacks, today_attacks, high_risk_count,
        live_sessions, avg_threat_score
    """
    db = get_db()
    
    total = db.attacks.count_documents({})
    
    # Today's attacks
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_count = db.attacks.count_documents({"created_at": {"$gte": today_start}})
    
    # High risk attacks (threat score >= 70)
    high_risk = db.attacks.count_documents({"threat_score": {"$gte": 70}})
    
    # Live sessions
    live = db.attacks.count_documents({"is_live": True})
    
    # Average threat score
    pipeline = [
        {"$group": {"_id": None, "avg_score": {"$avg": "$threat_score"}}}
    ]
    avg_result = list(db.attacks.aggregate(pipeline))
    avg_score = round(avg_result[0]["avg_score"], 1) if avg_result else 0
    
    return {
        "total_attacks": total,
        "today_attacks": today_count,
        "high_risk_attacks": high_risk,
        "live_sessions": live,
        "avg_threat_score": avg_score,
    }


def get_top_commands(limit=10):
    """Get most frequently used attacker commands."""
    db = get_db()
    pipeline = [
        {"$unwind": "$commands"},
        {"$group": {"_id": "$commands", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"command": "$_id", "count": 1, "_id": 0}},
    ]
    return list(db.attacks.aggregate(pipeline))


def get_top_ips(limit=10):
    """Get IPs with most attack sessions."""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$src_ip", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"ip": "$_id", "count": 1, "_id": 0}},
    ]
    return list(db.attacks.aggregate(pipeline))


def get_attack_timeline(days=30):
    """Get daily attack counts for the last N days."""
    db = get_db()
    from datetime import timedelta
    
    start_date = utc_now() - timedelta(days=days)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
            },
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$threat_score"},
        }},
        {"$sort": {"_id": 1}},
        {"$project": {"date": "$_id", "count": 1, "avg_score": 1, "_id": 0}},
    ]
    return list(db.attacks.aggregate(pipeline))


def get_stage_distribution():
    """Get distribution of attack stages."""
    db = get_db()
    pipeline = [
        {"$match": {"attack_stage": {"$ne": None}}},
        {"$group": {"_id": "$attack_stage", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$project": {"stage": "$_id", "count": 1, "_id": 0}},
    ]
    return list(db.attacks.aggregate(pipeline))


def get_intent_distribution():
    """Get distribution of detected intents."""
    db = get_db()
    pipeline = [
        {"$match": {"intent": {"$ne": None}}},
        {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$project": {"intent": "$_id", "count": 1, "_id": 0}},
    ]
    return list(db.attacks.aggregate(pipeline))
