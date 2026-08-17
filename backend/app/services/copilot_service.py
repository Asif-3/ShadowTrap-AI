"""
ShadowTrap AI - AI Security Copilot Service
=============================================
Orchestrates the complete AI analysis pipeline:
    1. Gathers session context + attacker history
    2. Runs existing deterministic analysis (stage, intent, score, prediction)
    3. Calls Qwen3-0.6B via llama.cpp for contextual reasoning
    4. Combines deterministic + AI predictions (hybrid)
    5. Stores analysis results
    6. Triggers Telegram alerts for high-value events

This service sits ON TOP of existing detection engines — it does NOT
replace stage detection, intent detection, threat scoring, or Markov
prediction. It enriches them with LLM reasoning.
"""

import threading
from app.extensions import get_db
from app.utils.helpers import utc_now, serialize_doc
from app.utils.logger import get_logger
from app.config import Config

logger = get_logger("services.copilot")

# Track in-flight analyses to prevent duplicate concurrent calls
_active_analyses = set()
_analysis_lock = threading.Lock()


def analyze_attack_session(session_id, app=None):
    """
    Run the full AI Security Copilot analysis for an attack session.
    
    This is the main orchestrator. It:
      1. Checks deduplication (don't re-analyze the same session concurrently)
      2. Fetches full session context from DB
      3. Correlates with previous events from same attacker IP
      4. Runs existing deterministic predictions
      5. Calls Qwen for contextual reasoning
      6. Stores the hybrid result
      7. Broadcasts via Socket.IO
      8. Triggers Telegram if threshold met
    
    Args:
        session_id: Attack session identifier
        app: Flask app instance (for background thread context)
        
    Returns:
        dict: Complete analysis result
    """
    # Deduplication — prevent concurrent analysis of the same session
    with _analysis_lock:
        if session_id in _active_analyses:
            logger.info(f"EVENT_CORRELATED session={session_id} — analysis already in progress, skipping")
            return None
        _active_analyses.add(session_id)
    
    try:
        return _run_analysis(session_id)
    finally:
        with _analysis_lock:
            _active_analyses.discard(session_id)


def _run_analysis(session_id):
    """Internal analysis execution."""
    from app.services.llm_service import analyze_security_event, _generate_fallback
    
    db = get_db()
    
    # 1. Fetch the attack record
    attack = db.attacks.find_one({"session_id": session_id})
    if not attack:
        logger.error(f"AI_ANALYSIS_FAILED session={session_id} — attack not found")
        return {"error": "Attack not found"}
    
    logger.info(f"EVENT_RECEIVED session={session_id} src_ip={attack.get('src_ip', '?')}")
    
    # 2. Check if already analyzed (dedup by checking existing analysis)
    existing = db.ai_analyses.find_one({"session_id": session_id})
    if existing and existing.get("source") == "qwen_llm":
        logger.debug(f"EVENT_CORRELATED session={session_id} — already analyzed by Qwen")
        return serialize_doc(existing)
    
    # 3. Gather full context
    session_data = _build_session_context(attack, db)
    
    # 4. Run the AI analysis (calls Qwen or falls back to deterministic)
    analysis = analyze_security_event(session_data)
    
    # 5. Enrich with hybrid prediction — merge deterministic + AI
    analysis = _enrich_hybrid_prediction(analysis, session_data)
    
    # 6. Store in ai_analyses collection
    analysis_doc = {
        "session_id": session_id,
        "src_ip": attack.get("src_ip", ""),
        **analysis,
        "analyzed_at": utc_now(),
    }
    
    db.ai_analyses.update_one(
        {"session_id": session_id},
        {"$set": analysis_doc},
        upsert=True,
    )
    
    # 7. Update the attack record with AI fields
    db.attacks.update_one(
        {"session_id": session_id},
        {"$set": {
            "ai_analysis": {
                "threat_level": analysis.get("threat_level"),
                "risk_score": analysis.get("risk_score"),
                "confidence": analysis.get("confidence"),
                "likely_next_move": analysis.get("likely_next_move"),
                "recommended_action": analysis.get("recommended_defensive_action"),
                "source": analysis.get("source"),
                "analyzed_at": utc_now().isoformat(),
            }
        }}
    )
    
    # 8. Broadcast via Socket.IO
    try:
        from app.socketio_events import broadcast_attack_update, broadcast_dashboard_update
        broadcast_attack_update(session_id, {
            "ai_analysis": analysis_doc,
            "status": "analyzed",
        })
        broadcast_dashboard_update()
    except Exception as e:
        logger.warning(f"Broadcast failed (non-critical): {e}")
    
    # 9. Trigger Telegram for high-value events
    threat_level = analysis.get("threat_level", "LOW")
    risk_score = analysis.get("risk_score", 0)
    
    if threat_level in ("HIGH", "CRITICAL") or risk_score >= Config.AI_ALERT_THRESHOLD:
        logger.info(f"NEXT_MOVE_PREDICTED session={session_id} threat={threat_level} score={risk_score}")
        try:
            from app.services.telegram_service import send_security_alert
            send_security_alert(attack, analysis)
        except Exception as e:
            logger.error(f"TELEGRAM_FAILED session={session_id} error={e}")
    
    return analysis_doc


def _build_session_context(attack, db):
    """
    Build rich session context for the AI copilot.
    Includes attacker history correlation.
    """
    session_id = attack.get("session_id", "")
    src_ip = attack.get("src_ip", "")
    commands = attack.get("commands", [])
    
    # Fetch existing deterministic analysis results
    stage_doc = db.attack_stages.find_one({"session_id": session_id}) or {}
    intent_doc = db.intents.find_one({"session_id": session_id}) or {}
    prediction_doc = db.predictions.find_one({"session_id": session_id}) or {}
    persona_doc = db.personas.find_one({"session_id": session_id}) or {}
    threat_doc = db.threat_scores.find_one({"session_id": session_id}) or {}
    mitre_doc = db.mitre_mappings.find_one({"session_id": session_id}) or {}
    
    # Correlate with previous events from the same IP
    previous_events = []
    if src_ip:
        prev_cursor = db.attacks.find(
            {"src_ip": src_ip, "session_id": {"$ne": session_id}},
            {"session_id": 1, "attack_stage": 1, "threat_score": 1, "commands": 1, "intent": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5)
        
        for doc in prev_cursor:
            previous_events.append({
                "session_id": doc.get("session_id"),
                "attack_stage": doc.get("attack_stage"),
                "threat_score": doc.get("threat_score", 0),
                "commands": doc.get("commands", []),
                "intent": doc.get("intent"),
            })
    
    if previous_events:
        logger.info(f"EVENT_CORRELATED session={session_id} — found {len(previous_events)} previous events from {src_ip}")
    
    return {
        "session_id": session_id,
        "src_ip": src_ip,
        "dst_port": attack.get("dst_port", 22),
        "protocol": attack.get("protocol", "ssh"),
        "username": attack.get("username", ""),
        "commands": commands,
        "start_time": str(attack.get("start_time", "")),
        "duration": attack.get("duration", 0),
        "downloaded_files": attack.get("downloaded_files", []),
        "attack_stage": stage_doc.get("stage", attack.get("attack_stage", "Unknown")),
        "intent": intent_doc.get("intent", attack.get("intent", "Unknown")),
        "threat_score": threat_doc.get("score", attack.get("threat_score", 0)),
        "persona": persona_doc if persona_doc else attack.get("persona", {}),
        "prediction": {
            "predicted_stage": prediction_doc.get("predicted_stage", ""),
            "confidence": prediction_doc.get("confidence", 0),
            "all_predictions": prediction_doc.get("all_predictions", []),
            "transition_chain": prediction_doc.get("transition_chain", []),
        },
        "mitre_mappings": mitre_doc.get("mappings", {}).get("techniques", []) if isinstance(mitre_doc.get("mappings"), dict) else [],
        "previous_events": previous_events,
    }


def _enrich_hybrid_prediction(analysis, session_data):
    """
    Merge deterministic prediction with AI reasoning.
    The deterministic prediction is authoritative; AI adds context.
    """
    prediction = session_data.get("prediction", {})
    
    if not prediction.get("predicted_stage"):
        return analysis
    
    # Add deterministic prediction alongside AI prediction
    analysis["deterministic_prediction"] = {
        "predicted_stage": prediction.get("predicted_stage"),
        "confidence": prediction.get("confidence"),
        "transition_chain": prediction.get("transition_chain", []),
    }
    
    return analysis


def analyze_attack_async(session_id, app):
    """
    Run copilot analysis in a background thread.
    Does NOT block the caller.
    
    Args:
        session_id: Attack session identifier
        app: Flask app instance (for app context in thread)
    """
    def _task():
        with app.app_context():
            try:
                analyze_attack_session(session_id, app)
            except Exception as e:
                logger.error(f"AI_ANALYSIS_FAILED session={session_id} (async): {e}")
    
    thread = threading.Thread(target=_task, daemon=True)
    thread.start()
    logger.info(f"AI_ANALYSIS_STARTED session={session_id} (async background)")
