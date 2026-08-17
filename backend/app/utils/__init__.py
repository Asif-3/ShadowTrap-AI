"""
ShadowTrap AI - Utils Package
"""

from app.utils.logger import get_logger
from app.utils.helpers import serialize_doc, serialize_docs, utc_now
from app.utils.validators import validate_email, validate_password, validate_ip
from app.utils.decorators import admin_required, role_required, handle_errors, validate_json

__all__ = [
    "get_logger",
    "serialize_doc",
    "serialize_docs",
    "utc_now",
    "validate_email",
    "validate_password",
    "validate_ip",
    "admin_required",
    "role_required",
    "handle_errors",
    "validate_json",
]
