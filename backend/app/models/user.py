"""
ShadowTrap AI - User Model
============================
MongoDB document schema and operations for user management.
"""

from datetime import datetime, timezone
import bcrypt
from app.extensions import get_db
from app.utils.helpers import serialize_doc, utc_now
from app.utils.logger import get_logger

logger = get_logger("models.user")


# ── Schema Definition ────────────────────────────────────
USER_SCHEMA = {
    "email": str,
    "password_hash": str,
    "name": str,
    "role": str,          # "admin" or "analyst"
    "avatar": str,        # URL or base64
    "is_active": bool,
    "created_at": datetime,
    "updated_at": datetime,
    "last_login": datetime,
}

VALID_ROLES = ["admin", "analyst"]


# ── User Operations ──────────────────────────────────────

def create_user(email, password, name, role="analyst"):
    """
    Create a new user in the database.
    
    Args:
        email: User email (unique)
        password: Plain text password (will be hashed)
        name: User's display name
        role: User role ('admin' or 'analyst')
        
    Returns:
        Created user document (serialized)
        
    Raises:
        ValueError: If email already exists or role is invalid
    """
    db = get_db()
    
    # Validate role
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
    
    # Check for existing user
    existing = db.users.find_one({"email": email.lower().strip()})
    if existing:
        raise ValueError("User with this email already exists")
    
    # Hash password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")
    
    now = utc_now()
    
    user_doc = {
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "name": name.strip(),
        "role": role,
        "avatar": "",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login": None,
    }
    
    result = db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    logger.info(f"User created: {email} (role: {role})")
    
    # Remove password hash from response
    safe_doc = {k: v for k, v in user_doc.items() if k != "password_hash"}
    return serialize_doc(safe_doc)


def find_user_by_email(email):
    """Find a user by email address."""
    db = get_db()
    return db.users.find_one({"email": email.lower().strip()})


def find_user_by_id(user_id):
    """Find a user by their ObjectId."""
    from bson import ObjectId
    db = get_db()
    return db.users.find_one({"_id": ObjectId(user_id)})


def verify_password(stored_hash, password):
    """
    Verify a password against a stored bcrypt hash.
    
    Args:
        stored_hash: Bcrypt hash from database
        password: Plain text password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        password.encode("utf-8"),
        stored_hash.encode("utf-8")
    )


def update_last_login(user_id):
    """Update the last login timestamp for a user."""
    from bson import ObjectId
    db = get_db()
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login": utc_now()}}
    )


def update_user(user_id, updates):
    """
    Update user fields.
    
    Args:
        user_id: User's ObjectId string
        updates: Dict of fields to update
        
    Returns:
        Updated user document (serialized, without password)
    """
    from bson import ObjectId
    db = get_db()
    
    # Prevent updating sensitive fields directly
    safe_fields = {"name", "avatar", "role", "is_active"}
    filtered_updates = {k: v for k, v in updates.items() if k in safe_fields}
    filtered_updates["updated_at"] = utc_now()
    
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": filtered_updates}
    )
    
    updated_user = find_user_by_id(user_id)
    if updated_user:
        safe_doc = {k: v for k, v in updated_user.items() if k != "password_hash"}
        return serialize_doc(safe_doc)
    return None


def update_password(user_id, new_password):
    """
    Update user password.
    
    Args:
        user_id: User's ObjectId string
        new_password: New plain text password
    """
    from bson import ObjectId
    db = get_db()
    
    password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")
    
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password_hash": password_hash,
            "updated_at": utc_now()
        }}
    )
    
    logger.info(f"Password updated for user: {user_id}")


def get_all_users():
    """Get all users (without password hashes)."""
    db = get_db()
    users = db.users.find({}, {"password_hash": 0})
    return [serialize_doc(u) for u in users]


def get_user_count():
    """Get total number of users."""
    db = get_db()
    return db.users.count_documents({})


def ensure_admin_exists(email, password, name="Admin"):
    """
    Ensure at least one admin user exists.
    Creates default admin if no admin users are found.
    
    Args:
        email: Admin email
        password: Admin password
        name: Admin display name
    """
    db = get_db()
    admin_count = db.users.count_documents({"role": "admin"})
    
    if admin_count == 0:
        try:
            create_user(email, password, name, role="admin")
            logger.info(f"Default admin created: {email}")
        except ValueError:
            # Admin already exists with this email
            logger.info(f"Admin user already exists: {email}")
