"""
ShadowTrap AI - Helpers Utility
================================
General helper functions used across the application.
"""

import json
import hashlib
from datetime import datetime, timezone
from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles MongoDB ObjectId and datetime."""
    
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize_doc(doc):
    """
    Serialize a MongoDB document for JSON response.
    Converts ObjectId to string and datetime to ISO format.
    
    Args:
        doc: MongoDB document (dict)
        
    Returns:
        Serialized dictionary
    """
    if doc is None:
        return None
    
    serialized = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_doc(value)
        elif isinstance(value, list):
            serialized[key] = [
                serialize_doc(item) if isinstance(item, dict) else
                str(item) if isinstance(item, ObjectId) else
                item.isoformat() if isinstance(item, datetime) else
                item
                for item in value
            ]
        else:
            serialized[key] = value
    
    return serialized


def serialize_docs(docs):
    """Serialize a list of MongoDB documents."""
    return [serialize_doc(doc) for doc in docs]


def utc_now():
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def make_utc_aware(dt):
    """
    Ensure a datetime object or ISO string is UTC timezone-aware.
    Converts naive datetimes (e.g. from MongoDB) or string ISO dates to UTC aware datetimes.
    """
    if not dt:
        return datetime.now(timezone.utc)
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    return datetime.now(timezone.utc)


def get_seconds_diff(dt1, dt2):
    """
    Safely calculate (dt1 - dt2) in seconds, handling naive and aware datetimes/strings.
    """
    t1 = make_utc_aware(dt1)
    t2 = make_utc_aware(dt2)
    return (t1 - t2).total_seconds()


def generate_session_hash(ip, timestamp):
    """
    Generate a deterministic session hash from IP and timestamp.
    
    Args:
        ip: Source IP address
        timestamp: Session start timestamp
        
    Returns:
        8-character hex hash string
    """
    raw = f"{ip}:{timestamp}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


def calculate_duration(start_time, end_time=None):
    """
    Calculate duration between two timestamps in seconds.
    
    Args:
        start_time: Start datetime
        end_time: End datetime (defaults to now)
        
    Returns:
        Duration in seconds (float)
    """
    if end_time is None:
        end_time = utc_now()
    
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)
    
    delta = end_time - start_time
    return max(0, delta.total_seconds())


def paginate_query(collection, query, page=1, per_page=20, sort_field="created_at", sort_order=-1):
    """
    Paginate a MongoDB query.
    
    Args:
        collection: MongoDB collection
        query: Query filter dict
        page: Page number (1-indexed)
        per_page: Items per page
        sort_field: Field to sort by
        sort_order: Sort order (1=asc, -1=desc)
        
    Returns:
        dict with items, total, page, per_page, total_pages
    """
    total = collection.count_documents(query)
    skip = (page - 1) * per_page
    
    items = list(
        collection.find(query)
        .sort(sort_field, sort_order)
        .skip(skip)
        .limit(per_page)
    )
    
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    return {
        "items": serialize_docs(items),
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


def format_bytes(size_bytes):
    """Format bytes to human-readable string."""
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def safe_get(data, *keys, default=None):
    """
    Safely navigate nested dictionaries.
    
    Args:
        data: Source dictionary
        *keys: Keys to traverse
        default: Default value if path doesn't exist
        
    Returns:
        Value at the nested key path, or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current
