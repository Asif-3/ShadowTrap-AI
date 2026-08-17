"""
ShadowTrap AI - Authentication Blueprint
==========================================
API routes for user authentication, registration, and session management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt
)
from app.services.auth_service import (
    login_user, register_user, refresh_access_token,
    get_current_user, change_password, forgot_password,
    reset_password
)
from app.utils.decorators import handle_errors, validate_json, admin_required
from app.utils.validators import validate_email, validate_password
from app.utils.logger import get_logger

logger = get_logger("blueprints.auth")

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ── Login ────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
@handle_errors
@validate_json("email", "password")
def login():
    """Authenticate user and return JWT tokens."""
    data = request.get_json()
    
    email = data["email"]
    password = data["password"]
    
    # Validate email format
    is_valid, error = validate_email(email)
    if not is_valid:
        return jsonify({"success": False, "error": error}), 400
    
    result = login_user(email, password)
    
    return jsonify({
        "success": True,
        "data": result,
        "message": "Login successful"
    }), 200


# ── Register ─────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
@handle_errors
@jwt_required()
@admin_required
@validate_json("email", "password", "name")
def register():
    """Register a new user (admin only)."""
    data = request.get_json()
    
    email = data["email"]
    password = data["password"]
    name = data["name"]
    role = data.get("role", "analyst")
    
    # Validate inputs
    is_valid, error = validate_email(email)
    if not is_valid:
        return jsonify({"success": False, "error": error}), 400
    
    is_valid, error = validate_password(password)
    if not is_valid:
        return jsonify({"success": False, "error": error}), 400
    
    user = register_user(email, password, name, role)
    
    return jsonify({
        "success": True,
        "data": user,
        "message": "User registered successfully"
    }), 201


# ── Get Current User ─────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@handle_errors
@jwt_required()
def me():
    """Get currently authenticated user's profile."""
    user_id = get_jwt_identity()
    user = get_current_user(user_id)
    
    return jsonify({
        "success": True,
        "data": user
    }), 200


# ── Get All Users ────────────────────────────────────────
@auth_bp.route("/users", methods=["GET"])
@handle_errors
@jwt_required()
def get_users():
    """Get all registered users for RBAC management."""
    from app.models.user import get_all_users
    users = get_all_users()
    return jsonify({
        "success": True,
        "data": users
    }), 200


# ── Refresh Token ────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
@handle_errors
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    result = refresh_access_token()
    
    return jsonify({
        "success": True,
        "data": result,
        "message": "Token refreshed"
    }), 200


# ── Change Password ──────────────────────────────────────
@auth_bp.route("/change-password", methods=["POST"])
@handle_errors
@jwt_required()
@validate_json("current_password", "new_password")
def change_pwd():
    """Change current user's password."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate new password strength
    is_valid, error = validate_password(data["new_password"])
    if not is_valid:
        return jsonify({"success": False, "error": error}), 400
    
    change_password(user_id, data["current_password"], data["new_password"])
    
    return jsonify({
        "success": True,
        "message": "Password changed successfully"
    }), 200


# ── Forgot Password ──────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["POST"])
@handle_errors
@validate_json("email")
def forgot_pwd():
    """Request password reset link."""
    data = request.get_json()
    result = forgot_password(data["email"])
    
    return jsonify({
        "success": True,
        "data": result,
        "message": result["message"]
    }), 200


# ── Reset Password ───────────────────────────────────────
@auth_bp.route("/reset-password", methods=["POST"])
@handle_errors
@validate_json("reset_token", "new_password")
def reset_pwd():
    """Reset password using a reset token."""
    data = request.get_json()
    
    is_valid, error = validate_password(data["new_password"])
    if not is_valid:
        return jsonify({"success": False, "error": error}), 400
    
    reset_password(data["reset_token"], data["new_password"])
    
    return jsonify({
        "success": True,
        "message": "Password reset successfully"
    }), 200


# ── Logout ───────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
@handle_errors
@jwt_required()
def logout():
    """Logout current user (client should discard tokens)."""
    user_id = get_jwt_identity()
    logger.info(f"User logged out: {user_id}")
    
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200
