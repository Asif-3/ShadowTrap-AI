"""
ShadowTrap AI - Analytics Blueprint
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.attack import (
    get_attack_timeline, get_stage_distribution,
    get_intent_distribution, get_top_commands, get_top_ips,
    get_attack_stats
)
from app.services.ip_intel_service import get_top_countries, get_top_isps
from app.extensions import get_db
from app.utils.decorators import handle_errors
from app.utils.helpers import serialize_docs

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/stats", methods=["GET"])
@analytics_bp.route("/overview", methods=["GET"])
@handle_errors
@jwt_required()
def overview():
    """Get comprehensive analytics overview."""
    db = get_db()
    total_attacks = db.attacks.count_documents({})
    live_sessions = db.attacks.count_documents({"is_live": True})
    
    # Calculate average threat score
    pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$threat_score"}}}]
    avg_result = list(db.attacks.aggregate(pipeline))
    avg_score = round(avg_result[0]["avg"], 1) if avg_result else 0
    
    return jsonify({
        "success": True,
        "data": {
            "total_attacks": total_attacks,
            "live_sessions": live_sessions,
            "avg_threat_score": avg_score,
            "stats": get_attack_stats(),
            "timeline": get_attack_timeline(30),
            "stage_distribution": get_stage_distribution(),
            "intent_distribution": get_intent_distribution(),
            "top_commands": get_top_commands(15),
            "top_ips": get_top_ips(15),
            "top_countries": get_top_countries(10),
            "top_isps": get_top_isps(10),
        }
    }), 200


@analytics_bp.route("/trends", methods=["GET"])
@handle_errors
@jwt_required()
def trends():
    """Get attack trend data."""
    days = request.args.get("days", 30, type=int)
    return jsonify({
        "success": True,
        "data": {
            "timeline": get_attack_timeline(days),
            "top_countries": get_top_countries(10),
            "top_isps": get_top_isps(10),
        }
    }), 200


@analytics_bp.route("/geo", methods=["GET"])
@handle_errors
@jwt_required()
def geo_data():
    """Get geographic attack distribution data."""
    db = get_db()
    pipeline = [
        {"$match": {"location.lat": {"$ne": 0}}},
        {"$project": {
            "ip": 1, "country": 1, "country_name": 1,
            "city": 1, "isp": 1, "location": 1, "_id": 0
        }},
    ]
    geo = list(db.ip_intelligence.aggregate(pipeline))
    return jsonify({"success": True, "data": geo}), 200


@analytics_bp.route("/heatmap", methods=["GET"])
@handle_errors
@jwt_required()
def heatmap():
    """Get hourly attack heatmap data (hour x day_of_week)."""
    db = get_db()
    pipeline = [
        {"$project": {
            "hour": {"$hour": "$created_at"},
            "dow": {"$dayOfWeek": "$created_at"},
        }},
        {"$group": {
            "_id": {"hour": "$hour", "dow": "$dow"},
            "count": {"$sum": 1},
        }},
        {"$project": {
            "hour": "$_id.hour", "day": "$_id.dow",
            "count": 1, "_id": 0,
        }},
    ]
    data = list(db.attacks.aggregate(pipeline))
    return jsonify({"success": True, "data": data}), 200
