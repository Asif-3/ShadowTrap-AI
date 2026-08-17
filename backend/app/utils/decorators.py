"""
ShadowTrap AI - Decorators Utility
====================================
Custom decorators for authentication, rate limiting, and error handling.
"""

from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.extensions import get_db
from app.utils.logger import get_logger

logger = get_logger("decorators")


def admin_required(fn):
    """
    Decorator to restrict access to admin users only.
    Must be used after @jwt_required().
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        role = claims.get("role", "analyst")
        
        if role != "admin":
            logger.warning(f"Unauthorized admin access attempt by user: {get_jwt_identity()}")
            return jsonify({
                "success": False,
                "error": "Admin access required",
                "code": "FORBIDDEN"
            }), 403
        
        return fn(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """
    Decorator to restrict access to specific roles.
    
    Usage:
        @role_required("admin", "analyst")
        def my_route():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role", "analyst")
            
            if role not in allowed_roles:
                logger.warning(
                    f"Role-restricted access denied. "
                    f"User: {get_jwt_identity()}, Role: {role}, "
                    f"Required: {allowed_roles}"
                )
                return jsonify({
                    "success": False,
                    "error": f"Access restricted to roles: {', '.join(allowed_roles)}",
                    "code": "FORBIDDEN"
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def handle_errors(fn):
    """
    Decorator to catch and format exceptions in route handlers.
    Provides consistent error response format.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error in {fn.__name__}: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "code": "VALIDATION_ERROR"
            }), 400
        except PermissionError as e:
            logger.error(f"Permission error in {fn.__name__}: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "code": "FORBIDDEN"
            }), 403
        except FileNotFoundError as e:
            logger.error(f"Not found error in {fn.__name__}: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "code": "NOT_FOUND"
            }), 404
        except Exception as e:
            logger.error(f"Unhandled error in {fn.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }), 500
    return wrapper


def validate_json(*required_fields):
    """
    Decorator to validate that request body contains required JSON fields.
    
    Usage:
        @validate_json("email", "password")
        def login():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True)
            
            if not data:
                return jsonify({
                    "success": False,
                    "error": "Request body must be valid JSON",
                    "code": "INVALID_JSON"
                }), 400
            
            missing = [f for f in required_fields if f not in data or not data[f]]
            if missing:
                return jsonify({
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing)}",
                    "code": "MISSING_FIELDS"
                }), 400
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
