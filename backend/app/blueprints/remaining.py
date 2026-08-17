"""
ShadowTrap AI - Persona, Prediction, Intent, Threat Score, LLM, IP Intel, Settings Blueprints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import get_db
from app.utils.decorators import handle_errors
from app.utils.helpers import serialize_doc, utc_now

# ── Persona Blueprint ────────────────────────────────────
persona_bp = Blueprint("persona", __name__, url_prefix="/api/persona")

@persona_bp.route("/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_persona(session_id):
    db = get_db()
    doc = db.personas.find_one({"session_id": session_id})
    if not doc:
        return jsonify({"success": False, "error": "Persona not found. Run analysis first."}), 404
    return jsonify({"success": True, "data": serialize_doc(doc)}), 200


# ── Prediction Blueprint ─────────────────────────────────
prediction_bp = Blueprint("prediction", __name__, url_prefix="/api/prediction")

@prediction_bp.route("/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_prediction(session_id):
    db = get_db()
    doc = db.predictions.find_one({"session_id": session_id})
    if not doc:
        return jsonify({"success": False, "error": "Prediction not found. Run analysis first."}), 404
    return jsonify({"success": True, "data": serialize_doc(doc)}), 200


# ── Intent Blueprint ─────────────────────────────────────
intent_bp = Blueprint("intent", __name__, url_prefix="/api/intent")

@intent_bp.route("/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_intent(session_id):
    db = get_db()
    doc = db.intents.find_one({"session_id": session_id})
    if not doc:
        return jsonify({"success": False, "error": "Intent not found. Run analysis first."}), 404
    return jsonify({"success": True, "data": serialize_doc(doc)}), 200


# ── Threat Score Blueprint ────────────────────────────────
threat_score_bp = Blueprint("threat_score", __name__, url_prefix="/api/threat-score")

@threat_score_bp.route("/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_threat_score(session_id):
    db = get_db()
    doc = db.threat_scores.find_one({"session_id": session_id})
    if not doc:
        return jsonify({"success": False, "error": "Threat score not found. Run analysis first."}), 404
    return jsonify({"success": True, "data": serialize_doc(doc)}), 200


# ── LLM Blueprint ────────────────────────────────────────
llm_bp = Blueprint("llm", __name__, url_prefix="/api/llm")

@llm_bp.route("/summary/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_llm_summary(session_id):
    db = get_db()
    doc = db.llm_summaries.find_one({"session_id": session_id})
    if not doc:
        return jsonify({"success": False, "error": "LLM summary not found. Run analysis first."}), 404
    return jsonify({"success": True, "data": serialize_doc(doc)}), 200

@llm_bp.route("/explain", methods=["POST"])
@handle_errors
@jwt_required()
def explain():
    from app.services.llm_service import generate_explanation
    data = request.get_json() or {}
    session_id = data.get("session_id", "")
    user_prompt = data.get("prompt", "")
    db = get_db()

    attack = None
    if session_id:
        attack = db.attacks.find_one({"session_id": session_id})
    
    if not attack:
        attack = db.attacks.find_one({}, sort=[("created_at", -1)])

    if not attack:
        return jsonify({
            "success": True,
            "data": {
                "explanation": f"Copilot analysis for '{user_prompt or 'General Query'}': No active honeypot attacks recorded yet in database. Decoy trap is currently listening for incoming connections.",
                "mitre_mappings": [],
                "recommended_actions": ["Keep honeypot operational", "Monitor decoy trap logs"]
            }
        }), 200

    llm_data = {
        "session_id": attack.get("session_id", "N/A"),
        "src_ip": attack.get("src_ip", "0.0.0.0"),
        "commands": attack.get("commands", []),
        "attack_stage": attack.get("attack_stage", "Reconnaissance"),
        "intent": attack.get("intent", "Discovery"),
        "persona": attack.get("persona", {}),
        "threat_score": attack.get("threat_score", 50),
        "user_prompt": user_prompt,
        "ip_intel": {},
        "mitre_mappings": [],
    }
    
    try:
        result = generate_explanation(llm_data)
        return jsonify({
            "success": True,
            "data": serialize_doc(result) if isinstance(result, dict) else {"explanation": str(result)}
        }), 200
    except Exception as e:
        from app.utils.logger import get_logger
        logger = get_logger("blueprints.llm")
        logger.error(f"LLM explain failed: {e}")
        return jsonify({
            "success": True,
            "data": {
                "explanation": f"AI model encountered an issue: {str(e)}. The system used rule-based analysis instead.",
                "is_fallback": True,
            }
        }), 200


@llm_bp.route("/status", methods=["GET"])
@handle_errors
@jwt_required()
def llm_status():
    from app.services.llm_service import get_llm_status
    status = get_llm_status()
    return jsonify({"success": True, "data": status}), 200

@llm_bp.route("/ai-analysis/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_ai_analysis(session_id):
    """Get the AI Security Copilot analysis for a session."""
    db = get_db()
    doc = db.ai_analyses.find_one({"session_id": session_id})
    if not doc:
        return jsonify({"success": False, "error": "AI analysis not found. Run analysis first."}), 404
    return jsonify({"success": True, "data": serialize_doc(doc)}), 200


# ── IP Intelligence Blueprint ────────────────────────────
ip_intel_bp = Blueprint("ip_intelligence", __name__, url_prefix="/api/ip-intel")

@ip_intel_bp.route("/<ip>", methods=["GET"])
@handle_errors
@jwt_required()
def get_ip_intel(ip):
    from app.services.ip_intel_service import lookup_ip
    result = lookup_ip(ip)
    return jsonify({"success": True, "data": result}), 200


# ── Settings Blueprint ───────────────────────────────────
settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

@settings_bp.route("", methods=["GET"])
@handle_errors
@jwt_required()
def get_settings():
    db = get_db()
    settings = list(db.settings.find({}, {"_id": 0}))
    if not settings:
        defaults = [
            {"key": "cowrie_log_path", "value": "./app/data/sample_cowrie_logs.json"},
            {"key": "llm_model", "value": "Qwen3-0.6B-Q4_K_M"},
            {"key": "alert_threshold", "value": "70"},
            {"key": "auto_analyze", "value": "true"},
            {"key": "report_format", "value": "pdf"},
        ]
        db.settings.insert_many(defaults)
        settings = defaults
    return jsonify({"success": True, "data": settings}), 200

@settings_bp.route("", methods=["PUT"])
@handle_errors
@jwt_required()
def update_settings():
    data = request.get_json()
    db = get_db()
    for key, value in data.items():
        db.settings.update_one(
            {"key": key},
            {"$set": {"key": key, "value": value, "updated_at": utc_now()}},
            upsert=True
        )
    return jsonify({"success": True, "message": "Settings updated"}), 200
