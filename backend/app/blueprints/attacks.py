"""
ShadowTrap AI - Attacks Blueprint
====================================
API routes for attack session management and analysis.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.attack import (
    get_attacks, get_attack_by_id, get_attack_by_session,
    get_live_attacks, get_recent_attacks, update_attack, delete_attacks
)
from app.ai.stage_detector import detect_stage, detect_all_stages_timeline
from app.ai.intent_detector import detect_intent
from app.ai.next_attack_predictor import predict_next_stage
from app.ai.persona_generator import generate_persona
from app.services.threat_score_service import calculate_threat_score
from app.services.ip_intel_service import lookup_ip
from app.services.mitre_service import map_commands
from app.services.deception_service import generate_deception_assets
from app.extensions import get_db
from app.utils.decorators import handle_errors
from app.utils.helpers import serialize_doc, utc_now
from app.utils.logger import get_logger

logger = get_logger("blueprints.attacks")

attacks_bp = Blueprint("attacks", __name__, url_prefix="/api/attacks")


@attacks_bp.route("", methods=["GET"])
@handle_errors
@jwt_required()
def list_attacks():
    """Get paginated list of attacks."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    # Build filters
    filters = {}
    if request.args.get("ip"):
        filters["src_ip"] = request.args.get("ip")
    if request.args.get("stage"):
        filters["attack_stage"] = request.args.get("stage")
    if request.args.get("intent"):
        filters["intent"] = request.args.get("intent")
    if request.args.get("min_score"):
        filters["threat_score"] = {"$gte": int(request.args.get("min_score"))}
    
    result = get_attacks(page, per_page, filters)
    
    return jsonify({
        "success": True,
        "data": result
    }), 200


@attacks_bp.route("/live", methods=["GET"])
@handle_errors
@jwt_required()
def live_sessions():
    """Get all currently active attack sessions."""
    attacks = get_live_attacks()
    
    return jsonify({
        "success": True,
        "data": attacks
    }), 200


@attacks_bp.route("/recent", methods=["GET"])
@handle_errors
@jwt_required()
def recent_attacks():
    """Get recent attacks."""
    limit = request.args.get("limit", 10, type=int)
    attacks = get_recent_attacks(limit)
    
    return jsonify({
        "success": True,
        "data": attacks
    }), 200


@attacks_bp.route("/<attack_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_attack(attack_id):
    """Get full attack details with all analysis."""
    # Try by ObjectId first, then by session_id
    attack = get_attack_by_id(attack_id) if len(attack_id) == 24 else None
    if not attack:
        attack = get_attack_by_session(attack_id)
    
    if not attack:
        return jsonify({"success": False, "error": "Attack not found"}), 404
    
    return jsonify({
        "success": True,
        "data": attack
    }), 200


@attacks_bp.route("/<attack_id>/analyze", methods=["POST"])
@handle_errors
@jwt_required()
def analyze_attack(attack_id):
    """Run full AI analysis pipeline on an attack session."""
    attack = get_attack_by_id(attack_id) if len(attack_id) == 24 else None
    if not attack:
        attack = get_attack_by_session(attack_id)
    
    if not attack:
        return jsonify({"success": False, "error": "Attack not found"}), 404
    
    commands = attack.get("commands", [])
    session_id = attack.get("session_id", "")
    src_ip = attack.get("src_ip", "")
    duration = attack.get("duration", 0)
    timestamps = attack.get("timestamps", [])
    
    db = get_db()
    
    # 1. Attack Stage Detection
    stage_result = detect_stage(commands)
    db.attack_stages.update_one(
        {"session_id": session_id},
        {"$set": {**stage_result, "session_id": session_id, "detected_at": utc_now()}},
        upsert=True
    )
    
    # 2. Intent Detection
    intent_result = detect_intent(commands)
    db.intents.update_one(
        {"session_id": session_id},
        {"$set": {**intent_result, "session_id": session_id, "detected_at": utc_now()}},
        upsert=True
    )
    
    # 3. Next Attack Prediction
    prediction_result = predict_next_stage(stage_result["stage"])
    db.predictions.update_one(
        {"session_id": session_id},
        {"$set": {**prediction_result, "session_id": session_id, "predicted_at": utc_now()}},
        upsert=True
    )
    
    # 4. Persona Generation
    persona_result = generate_persona(commands, duration, timestamps)
    db.personas.update_one(
        {"session_id": session_id},
        {"$set": {**persona_result, "session_id": session_id, "generated_at": utc_now()}},
        upsert=True
    )
    
    # 5. Threat Score
    score_data = {
        "commands": commands,
        "duration": duration,
        "attack_stage": stage_result["stage"],
        "intent": intent_result["intent"],
        "persona": persona_result,
        "downloaded_files": attack.get("downloaded_files", []),
    }
    threat_result = calculate_threat_score(score_data)
    db.threat_scores.update_one(
        {"session_id": session_id},
        {"$set": {**threat_result, "session_id": session_id, "calculated_at": utc_now()}},
        upsert=True
    )
    
    # 6. IP Intelligence
    ip_intel = {}
    if src_ip:
        ip_intel = lookup_ip(src_ip)
    
    # 7. MITRE Mapping
    mitre_result = map_commands(commands)
    
    # 8. Deception Assets
    deception = generate_deception_assets(
        intent_result["intent"], stage_result["stage"], commands
    )
    
    # 9. Stage Timeline
    stage_timeline = detect_all_stages_timeline(commands, timestamps)
    
    # Update attack record with analysis results
    update_attack(session_id, {
        "attack_stage": stage_result["stage"],
        "intent": intent_result["intent"],
        "persona": persona_result,
        "threat_score": threat_result["score"],
        "prediction": prediction_result,
        "mitre": mitre_result,
        "status": "analyzed",
    })
    
    # 10. AI Security Copilot (async — calls Qwen3-0.6B via llama.cpp in background)
    from flask import current_app
    from app.services.copilot_service import analyze_attack_async
    
    app_context = current_app._get_current_object()
    analyze_attack_async(session_id, app_context)
    
    llm_result = {
        "attack_summary": "AI analysis in progress — the copilot is generating a detailed threat report...",
        "status": "generating",
    }
    
    return jsonify({
        "success": True,
        "data": {
            "session_id": session_id,
            "stage": stage_result,
            "intent": intent_result,
            "prediction": prediction_result,
            "persona": persona_result,
            "threat_score": threat_result,
            "ip_intel": ip_intel,
            "mitre": mitre_result,
            "deception": deception,
            "stage_timeline": stage_timeline,
            "llm": llm_result,
        },
        "message": "Analysis complete"
    }), 200


@attacks_bp.route("", methods=["DELETE"])
@handle_errors
@jwt_required()
def bulk_delete_attacks():
    """Bulk delete attack sessions by ID."""
    data = request.get_json() or {}
    session_ids = data.get("session_ids", [])
    
    if not session_ids:
        return jsonify({"success": False, "error": "No session IDs provided"}), 400
        
    delete_attacks(session_ids)
    
    return jsonify({
        "success": True,
        "message": f"Successfully deleted {len(session_ids)} attack sessions"
    }), 200
