"""
ShadowTrap AI - Report Model
===============================
MongoDB operations for generated security reports.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.extensions import get_db
from app.utils.helpers import serialize_doc, serialize_docs, utc_now, paginate_query
from app.utils.logger import get_logger

logger = get_logger("models.report")


def create_report(report_data):
    """Create a new report record."""
    db = get_db()
    now = utc_now()
    
    doc = {
        "session_id": report_data.get("session_id", ""),
        "title": report_data.get("title", "Security Report"),
        "type": report_data.get("type", "full"),  # full, summary, incident
        "format": report_data.get("format", "pdf"),  # pdf, html, json
        "file_path": report_data.get("file_path", ""),
        "file_size": report_data.get("file_size", 0),
        "generated_by": report_data.get("generated_by", "system"),
        "attack_data": report_data.get("attack_data", {}),
        "generated_at": now,
        "created_at": now,
    }
    
    result = db.reports.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info(f"Report created: {doc['title']} ({doc['format']})")
    return serialize_doc(doc)


def get_report_by_id(report_id):
    """Get a report by its ObjectId, filename, or ID string."""
    db = get_db()
    doc = None
    if isinstance(report_id, str) and len(report_id) == 24:
        try:
            doc = db.reports.find_one({"_id": ObjectId(report_id)})
        except Exception:
            pass
    if not doc:
        doc = db.reports.find_one({"filename": report_id})
    if not doc:
        doc = db.reports.find_one({"session_id": report_id})
    return serialize_doc(doc) if doc else None


def sync_reports_from_disk():
    """Sync all report files from backend/reports folder into MongoDB."""
    import os
    db = get_db()
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    reports_dir = os.path.join(backend_dir, "reports")
    if not os.path.exists(reports_dir):
        return

    for filename in os.listdir(reports_dir):
        filepath = os.path.abspath(os.path.join(reports_dir, filename))
        if not os.path.isfile(filepath):
            continue

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
        if ext not in ["pdf", "html", "json", "txt"]:
            continue

        # Check if already registered
        existing = db.reports.find_one({"filename": filename})
        if not existing:
            # Parse session_id from filename e.g. ShadowTrap_Report_<session_id>_<timestamp>.<ext>
            session_id = "UNKNOWN"
            if filename.startswith("ShadowTrap_Report_"):
                parts = filename.replace("ShadowTrap_Report_", "").split("_")
                if parts:
                    session_id = parts[0]
            
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
            file_size = os.path.getsize(filepath)

            doc = {
                "session_id": session_id,
                "title": f"Incident Report — {session_id}",
                "type": "incident",
                "format": ext,
                "filename": filename,
                "file_path": filepath,
                "file_size": file_size,
                "generated_by": "system",
                "generated_at": mtime,
                "created_at": mtime,
                "download_count": 0,
                "downloaded": False,
            }
            db.reports.insert_one(doc)
            logger.info(f"Synced report from disk: {filename}")


def record_report_download(report_id):
    """Record a download event for a report in MongoDB."""
    db = get_db()
    now = utc_now()
    if isinstance(report_id, str) and len(report_id) == 24:
        try:
            db.reports.update_one(
                {"_id": ObjectId(report_id)},
                {"$inc": {"download_count": 1}, "$set": {"downloaded": True, "last_downloaded_at": now}}
            )
            return
        except Exception:
            pass
    db.reports.update_one(
        {"$or": [{"filename": report_id}, {"session_id": report_id}]},
        {"$inc": {"download_count": 1}, "$set": {"downloaded": True, "last_downloaded_at": now}}
    )


def get_reports(page=1, per_page=20, filters=None):
    """Get paginated list of reports."""
    try:
        sync_reports_from_disk()
    except Exception as e:
        logger.warning(f"Error syncing reports from disk: {e}")
    db = get_db()
    query = filters or {}
    return paginate_query(db.reports, query, page, per_page, "generated_at", -1)


def get_recent_reports(limit=5):
    """Get most recent reports."""
    db = get_db()
    docs = db.reports.find().sort("generated_at", -1).limit(limit)
    return serialize_docs(list(docs))


def delete_report(report_id):
    """Delete a report by ID."""
    db = get_db()
    result = db.reports.delete_one({"_id": ObjectId(report_id)})
    return result.deleted_count > 0


def get_report_count():
    """Get total report count."""
    db = get_db()
    return db.reports.count_documents({})

