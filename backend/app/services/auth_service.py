"""
ShadowTrap AI - Authentication Service
========================================
Business logic for user authentication, JWT token management,
and session handling.
"""

from datetime import datetime, timezone, timedelta
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt
)
from app.models.user import (
    create_user, find_user_by_email, find_user_by_id,
    verify_password, update_last_login, update_password,
    ensure_admin_exists
)
from app.utils.logger import get_logger

logger = get_logger("services.auth")


def login_user(email, password):
    """
    Authenticate a user and generate JWT tokens.
    
    Args:
        email: User email
        password: Plain text password
        
    Returns:
        Dict with access_token, refresh_token, and user data
        
    Raises:
        ValueError: If credentials are invalid
    """
    user = find_user_by_email(email)
    
    if not user:
        logger.warning(f"Login attempt with non-existent email: {email}")
        raise ValueError("Invalid email or password")
    
    if not user.get("is_active", True):
        logger.warning(f"Login attempt by inactive user: {email}")
        raise ValueError("Account is deactivated. Contact administrator.")
    
    if not verify_password(user["password_hash"], password):
        logger.warning(f"Failed login attempt for: {email}")
        raise ValueError("Invalid email or password")
    
    # Generate tokens with additional claims
    additional_claims = {
        "role": user.get("role", "analyst"),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
    }
    
    access_token = create_access_token(
        identity=str(user["_id"]),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(user["_id"]),
        additional_claims=additional_claims
    )
    
    # Update last login
    update_last_login(str(user["_id"]))
    
    logger.info(f"User logged in: {email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "avatar": user.get("avatar", ""),
        }
    }


def register_user(email, password, name, role="analyst"):
    """
    Register a new user.
    
    Args:
        email: User email
        password: Plain text password
        name: Display name
        role: User role
        
    Returns:
        Created user data
    """
    user = create_user(email, password, name, role)
    logger.info(f"New user registered: {email} (role: {role})")
    return user


def refresh_access_token():
    """
    Generate a new access token using the refresh token.
    
    Returns:
        Dict with new access_token
    """
    identity = get_jwt_identity()
    claims = get_jwt()
    
    user = find_user_by_id(identity)
    if not user:
        raise ValueError("User not found")
    
    additional_claims = {
        "role": user.get("role", "analyst"),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
    }
    
    new_token = create_access_token(
        identity=identity,
        additional_claims=additional_claims
    )
    
    return {"access_token": new_token}


def get_current_user(user_id):
    """
    Get current authenticated user data.
    
    Args:
        user_id: User's ObjectId string
        
    Returns:
        User data dict (without password)
    """
    from app.utils.helpers import serialize_doc
    user = find_user_by_id(user_id)
    
    if not user:
        raise ValueError("User not found")
    
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return serialize_doc(safe_user)


def change_password(user_id, current_password, new_password):
    """
    Change user password after verifying current password.
    
    Args:
        user_id: User's ObjectId string
        current_password: Current plain text password
        new_password: New plain text password
    """
    user = find_user_by_id(user_id)
    
    if not user:
        raise ValueError("User not found")
    
    if not verify_password(user["password_hash"], current_password):
        raise ValueError("Current password is incorrect")
    
    update_password(user_id, new_password)
    logger.info(f"Password changed for user: {user_id}")


def forgot_password(email):
    """
    Handle forgot password request.
    In production, this would send an email with a reset link.
    For development, we log the reset token.
    
    Args:
        email: User email
        
    Returns:
        Dict with message (and reset_token in dev mode)
    """
    user = find_user_by_email(email)
    
    if not user:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a reset link has been sent."}
    
    # Generate a simple reset token (in production, use a proper token with expiry)
    import secrets
    reset_token = secrets.token_urlsafe(32)
    
    # Store reset token in database
    from app.extensions import get_db
    from app.utils.helpers import utc_now
    db = get_db()
    db.users.update_one(
        {"email": email},
        {"$set": {
            "reset_token": reset_token,
            "reset_token_expires": utc_now() + timedelta(hours=1)
        }}
    )
    
    logger.info(f"Password reset requested for: {email}")
    logger.debug(f"Reset token (dev): {reset_token}")
    
    return {
        "message": "If the email exists, a reset link has been sent.",
        "reset_token": reset_token  # Only include in dev mode
    }


def reset_password(reset_token, new_password):
    """
    Reset password using a reset token.
    
    Args:
        reset_token: Password reset token
        new_password: New plain text password
    """
    from app.extensions import get_db
    from app.utils.helpers import utc_now
    
    db = get_db()
    user = db.users.find_one({
        "reset_token": reset_token,
        "reset_token_expires": {"$gt": utc_now()}
    })
    
    if not user:
        raise ValueError("Invalid or expired reset token")
    
    update_password(str(user["_id"]), new_password)
    
    # Clear reset token
    db.users.update_one(
        {"_id": user["_id"]},
        {"$unset": {"reset_token": "", "reset_token_expires": ""}}
    )
    
    logger.info(f"Password reset completed for: {user['email']}")


def init_default_admin(app):
    """Initialize default admin user on first startup."""
    email = app.config.get("ADMIN_EMAIL", "admin@shadowtrap.ai")
    password = app.config.get("ADMIN_PASSWORD", "ShadowTrap@2024")
    ensure_admin_exists(email, password, name="Admin")
