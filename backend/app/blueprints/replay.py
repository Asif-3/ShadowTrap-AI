"""
ShadowTrap AI - Replay Blueprint
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.services.cowrie_service import get_session_replay
from app.extensions import get_db
from app.utils.decorators import handle_errors

replay_bp = Blueprint("replay", __name__, url_prefix="/api/replay")


@replay_bp.route("/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_replay(session_id):
    """Get attack replay data for terminal-style playback."""
    db = get_db()
    replay = get_session_replay(session_id, db.attacks)
    if not replay:
        return jsonify({"success": False, "error": "Session not found"}), 404
    return jsonify({"success": True, "data": replay}), 200
