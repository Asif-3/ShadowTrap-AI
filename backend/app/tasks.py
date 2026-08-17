"""
ShadowTrap AI X — Background Tasks
=====================================
Defines async/sync tasks for AI analysis, model training,
report generation, and IP intelligence lookups.

Tasks run via Celery when available, or synchronously as fallback.
"""

from app.utils.logger import get_logger
from app.config import Config

logger = get_logger("tasks")


def analyze_session(session_id):
    """
    Run full AI analysis pipeline on an attack session.
    
    Pipeline:
        1. Feature extraction
        2. Behavior embedding
        3. Stage detection
        4. Intent detection
        5. Persona generation
        6. Threat scoring
        7. MITRE mapping
        8. Next attack prediction
        9. Anomaly detection
        10. Knowledge graph update
        11. LLM explanation (if API key configured)
        12. Deception asset generation
    
    Args:
        session_id: Attack session identifier
        
    Returns:
        dict: Analysis results summary
    """
    from app.extensions import get_db
    from app.ai.stage_detector import detect_stage
    from app.ai.intent_detector import detect_intent
    from app.ai.persona_generator import generate_persona
    from app.ai.next_attack_predictor import predict_next_stage
    from app.services.threat_score_service import calculate_threat_score
    from app.services.mitre_service import map_commands
    from app.services.deception_service import generate_deception_assets
    from app.utils.helpers import utc_now
    
    db = get_db()
    
    # Fetch the attack record
    attack = db.attacks.find_one({"session_id": session_id})
    if not attack:
        logger.error(f"Attack not found for analysis: {session_id}")
        return {"error": "Attack not found"}
    
    commands = attack.get("commands", [])
    duration = attack.get("duration", 0)
    
    logger.info(f"Starting analysis pipeline for session: {session_id}")
    
    results = {}
    
    # 1. Stage Detection
    stage_result = detect_stage(commands)
    results["stage"] = stage_result
    db.attack_stages.update_one(
        {"session_id": session_id},
        {"$set": {**stage_result, "session_id": session_id, "detected_at": utc_now()}},
        upsert=True
    )
    
    # 2. Intent Detection
    intent_result = detect_intent(commands)
    results["intent"] = intent_result
    db.intents.update_one(
        {"session_id": session_id},
        {"$set": {**intent_result, "session_id": session_id, "detected_at": utc_now()}},
        upsert=True
    )
    
    # 3. Persona Generation
    persona_result = generate_persona(commands, duration)
    results["persona"] = persona_result
    db.personas.update_one(
        {"session_id": session_id},
        {"$set": {**persona_result, "session_id": session_id, "generated_at": utc_now()}},
        upsert=True
    )
    
    # 4. Threat Scoring
    score_data = {
        "commands": commands,
        "duration": duration,
        "attack_stage": stage_result["stage"],
        "intent": intent_result["intent"],
        "persona": persona_result,
        "downloaded_files": attack.get("downloaded_files", []),
    }
    threat_result = calculate_threat_score(score_data)
    results["threat_score"] = threat_result
    db.threat_scores.update_one(
        {"session_id": session_id},
        {"$set": {**threat_result, "session_id": session_id, "calculated_at": utc_now()}},
        upsert=True
    )
    
    # 5. MITRE Mapping
    mitre_result = map_commands(commands)
    results["mitre"] = mitre_result
    db.mitre_mappings.update_one(
        {"session_id": session_id},
        {"$set": {
            "session_id": session_id,
            "mappings": mitre_result,
            "mapped_at": utc_now(),
        }},
        upsert=True
    )
    
    # 6. Next Attack Prediction
    prediction_result = predict_next_stage(stage_result["stage"])
    results["prediction"] = prediction_result
    db.predictions.update_one(
        {"session_id": session_id},
        {"$set": {**prediction_result, "session_id": session_id, "predicted_at": utc_now()}},
        upsert=True
    )
    
    # 7. Deception Assets
    deception_result = generate_deception_assets(
        intent_result["intent"],
        stage_result["stage"],
        commands
    )
    results["deception"] = deception_result
    
    # 8. Behavior Embedding (graceful — may not be available)
    try:
        from app.ai.behavior_embedding import generate_embedding
        embedding_result = generate_embedding(commands)
        results["embedding"] = {"status": "generated"}
        db.embeddings.update_one(
            {"session_id": session_id},
            {"$set": {
                "session_id": session_id,
                "embedding": embedding_result.get("embedding", []),
                "method": embedding_result.get("method", "tfidf"),
                "generated_at": utc_now(),
            }},
            upsert=True
        )
    except Exception as e:
        logger.warning(f"Embedding generation skipped: {e}")
        results["embedding"] = {"status": "skipped"}
    
    # 9. Anomaly Detection (graceful)
    try:
        from app.ai.anomaly_detector import detect_anomaly
        anomaly_result = detect_anomaly(commands)
        results["anomaly"] = anomaly_result
        db.behavior_features.update_one(
            {"session_id": session_id},
            {"$set": {
                "session_id": session_id,
                "is_anomaly": anomaly_result.get("is_anomaly", False),
                "anomaly_score": anomaly_result.get("anomaly_score", 0),
                "cluster_id": anomaly_result.get("cluster_id", -1),
                "analyzed_at": utc_now(),
            }},
            upsert=True
        )
    except Exception as e:
        logger.warning(f"Anomaly detection skipped: {e}")
        results["anomaly"] = {"status": "skipped"}
    
    # 10. Update attack record with analysis results
    db.attacks.update_one(
        {"session_id": session_id},
        {"$set": {
            "attack_stage": stage_result["stage"],
            "intent": intent_result["intent"],
            "persona": persona_result,
            "threat_score": threat_result["score"],
            "status": "analyzed",
            "updated_at": utc_now(),
        }}
    )
    
    # 11. Broadcast real-time update
    try:
        from app.socketio_events import broadcast_analysis_complete, broadcast_dashboard_update
        broadcast_analysis_complete(session_id, {
            "stage": stage_result["stage"],
            "intent": intent_result["intent"],
            "threat_score": threat_result["score"],
            "persona_name": persona_result.get("persona_name", "Unknown"),
        })
        
        # Send threat alert if high risk
        if threat_result["score"] >= 70:
            from app.socketio_events import broadcast_threat_alert
            broadcast_threat_alert({
                "session_id": session_id,
                "severity": "critical" if threat_result["score"] >= 85 else "high",
                "title": f"High-Risk Attack Detected ({threat_result['score']}/100)",
                "message": f"Session {session_id} classified as {stage_result['stage']} with {intent_result['intent']} intent.",
                "threat_score": threat_result["score"],
            })
        
        broadcast_dashboard_update()
    except Exception as e:
        logger.warning(f"Broadcast failed (non-critical): {e}")
    
    logger.info(f"✅ Analysis complete for session: {session_id} "
                f"(stage={stage_result['stage']}, score={threat_result['score']})")
    
    # 12. AI Security Copilot (Qwen3-0.6B via llama.cpp) — only for high-value sessions
    if threat_result["score"] >= Config.AI_ALERT_THRESHOLD:
        try:
            from app.services.copilot_service import analyze_attack_session
            copilot_result = analyze_attack_session(session_id)
            results["copilot"] = {"status": "completed"}
            logger.info(f"Copilot analysis completed for session: {session_id}")
        except Exception as e:
            logger.warning(f"Copilot analysis skipped: {e}")
            results["copilot"] = {"status": "skipped", "reason": str(e)}
    else:
        results["copilot"] = {"status": "skipped", "reason": "Below alert threshold"}
    
    return results


def train_models():
    """
    Trigger self-learning model training pipeline.
    
    Trains/retrains ML models using accumulated attack data.
    """
    try:
        from app.ai.self_learning import run_training_pipeline
        result = run_training_pipeline()
        
        from app.socketio_events import broadcast_model_update
        broadcast_model_update({
            "model_name": "ensemble",
            "status": "completed",
            "accuracy": result.get("accuracy", 0),
            "version": result.get("version", "1.0"),
        })
        
        return result
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return {"error": str(e)}


def generate_report_task(session_id, format_type="pdf"):
    """
    Generate investigation report in background.
    
    Args:
        session_id: Attack session identifier
        format_type: Report format ("pdf", "html", "json")
        
    Returns:
        dict: Report metadata with file path
    """
    from app.services.report_service import generate_report
    return generate_report(session_id, format_type)


def batch_ip_lookup(ip_list):
    """
    Perform IP intelligence lookup for multiple IPs.
    
    Args:
        ip_list: List of IP address strings
        
    Returns:
        dict: IP-to-intelligence mapping
    """
    from app.services.ip_intel_service import lookup_ip
    
    results = {}
    for ip in ip_list:
        try:
            results[ip] = lookup_ip(ip)
        except Exception as e:
            logger.warning(f"IP lookup failed for {ip}: {e}")
            results[ip] = {"error": str(e)}
    
    return results
