"""
ShadowTrap AI X — Flask Application Factory
=============================================
Creates and configures the Flask application with all blueprints,
extensions, Socket.IO, and middleware.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import get_config
from app.extensions import init_mongodb, init_jwt, init_socketio, socketio
from app.utils.logger import get_logger

logger = get_logger("app")


def create_app(config_class=None):
    """
    Flask application factory.
    
    Args:
        config_class: Configuration class (defaults to auto-detect)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize CORS
    CORS(app, origins=app.config.get("CORS_ORIGINS", ["*"]),
         supports_credentials=True, expose_headers=["Content-Disposition", "Content-Type"])
    
    # Initialize extensions
    init_mongodb(app)
    init_jwt(app)
    init_socketio(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register Socket.IO event handlers
    _register_socketio_events()
    
    # Create default admin user
    with app.app_context():
        from app.services.auth_service import init_default_admin
        init_default_admin(app)
        
        # Seed sample data on first run
        _seed_sample_data(app)
    
    # Ensure reports directory exists
    reports_dir = app.config.get("REPORT_STORAGE_PATH", "./reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    logger.info("🛡️  ShadowTrap AI X initialized successfully")
    
    return app


def _register_blueprints(app):
    """Register all API blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.attacks import attacks_bp
    from app.blueprints.replay import replay_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.remaining import (
        persona_bp, prediction_bp, intent_bp,
        threat_score_bp, llm_bp, ip_intel_bp, settings_bp
    )
    from app.blueprints.knowledge_graph import knowledge_graph_bp
    from app.blueprints.threat_intel import threat_intel_bp
    from app.blueprints.ai_models import ai_models_bp
    from app.blueprints.trap import trap_bp
    
    blueprints = [
        auth_bp, dashboard_bp, attacks_bp, replay_bp,
        analytics_bp, reports_bp, persona_bp, prediction_bp,
        intent_bp, threat_score_bp, llm_bp, ip_intel_bp, settings_bp,
        knowledge_graph_bp, threat_intel_bp, ai_models_bp, trap_bp,
    ]
    
    for bp in blueprints:
        app.register_blueprint(bp)
        logger.debug(f"Registered blueprint: {bp.name}")
    
    # Health check route
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "ShadowTrap AI X",
            "version": "2.0.0"
        }), 200

    # Decoy Admin Login Routes for Hydra Brute Force
    from app.blueprints.trap import admin_login_trap
    app.add_url_rule("/admin-login", endpoint="admin_login_root", view_func=admin_login_trap, methods=["GET", "POST"])
    app.add_url_rule("/login", endpoint="login_root", view_func=admin_login_trap, methods=["GET", "POST"])
    app.add_url_rule("/decoy-login", endpoint="decoy_login_root", view_func=admin_login_trap, methods=["GET", "POST"])

    logger.info(f"Registered {len(blueprints)} blueprints")


def _register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": "Bad request",
            "code": "BAD_REQUEST"
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "error": "Authentication required",
            "code": "UNAUTHORIZED"
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "success": False,
            "error": "Access forbidden",
            "code": "FORBIDDEN"
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        from flask import request
        _record_http_probe(request)
        return jsonify({
            "success": False,
            "error": "Resource not found",
            "code": "NOT_FOUND"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }), 500


def _record_http_probe(req):
    """Record HTTP scanner probes (e.g. Nmap/Nikto scans) as real attack sessions."""
    try:
        from app.extensions import get_db
        from app.models.attack import create_attack
        from app.ai.stage_detector import detect_stage
        from app.ai.intent_detector import detect_intent
        from app.services.threat_score_service import calculate_threat_score
        from app.socketio_events import broadcast_new_attack, broadcast_attack_update, broadcast_dashboard_update
        from app.utils.helpers import utc_now, make_utc_aware

        src_ip = req.remote_addr or "unknown"
        path = req.path
        method = req.method
        user_agent = req.headers.get("User-Agent", "")

        # Skip recording static frontend assets
        if path.startswith("/assets/") or path.endswith(".js") or path.endswith(".css") or path.endswith(".ico"):
            return

        db = get_db()
        session_id = f"SCAN-HTTP-{src_ip.replace('.', '')}"
        cmd_str = f"{method} {path}"
        if user_agent:
            cmd_str += f" (UA: {user_agent[:40]})"

        existing = db.attacks.find_one({"session_id": session_id})
        now = utc_now()

        if existing:
            commands = existing.get("commands", [])
            if cmd_str not in commands:
                commands.append(cmd_str)
            timestamps = existing.get("timestamps", [])
            timestamps.append(now.isoformat())

            stage_res = detect_stage(commands)
            intent_res = detect_intent(commands)
            created_at = make_utc_aware(existing.get("created_at", now))
            threat_res = calculate_threat_score({
                "commands": commands,
                "duration": (now - created_at).total_seconds(),
                "attack_stage": stage_res["stage"],
                "intent": intent_res["intent"],
                "persona": existing.get("persona") or {},
                "downloaded_files": [],
            })

            new_score = max(existing.get("threat_score", 0), threat_res["score"], 45)
            db.attacks.update_one(
                {"session_id": session_id},
                {"$set": {
                    "commands": commands,
                    "command_count": len(commands),
                    "timestamps": timestamps,
                    "attack_stage": stage_res["stage"],
                    "intent": intent_res["intent"],
                    "threat_score": new_score,
                    "status": "analyzed",
                    "updated_at": now,
                }}
            )
            broadcast_attack_update(session_id, {
                "commands": commands,
                "command_count": len(commands),
                "threat_score": new_score,
                "attack_stage": stage_res["stage"],
                "intent": intent_res["intent"],
            })
            broadcast_dashboard_update()
        else:
            commands = [cmd_str]
            stage_res = detect_stage(commands)
            intent_res = detect_intent(commands)
            threat_res = calculate_threat_score({
                "commands": commands,
                "duration": 1,
                "attack_stage": stage_res["stage"],
                "intent": intent_res["intent"],
                "persona": {},
                "downloaded_files": [],
            })
            attack_doc = {
                "session_id": session_id,
                "src_ip": src_ip,
                "src_port": req.environ.get("REMOTE_PORT", 0),
                "dst_port": 5000,
                "protocol": "HTTP",
                "username": "",
                "password": "",
                "commands": commands,
                "timestamps": [now.isoformat()],
                "downloaded_files": [],
                "executed_files": [],
                "start_time": now,
                "duration": 1,
                "command_count": 1,
                "status": "analyzed",
                "threat_score": max(45, threat_res["score"]),
                "attack_stage": stage_res["stage"],
                "intent": intent_res["intent"],
                "persona": {
                    "skill_level": "Intermediate",
                    "attack_style": "Nmap / Web Reconnaissance",
                    "persistence_level": "Medium"
                },
                "is_live": True,
                "created_at": now,
                "updated_at": now,
            }
            create_attack(attack_doc)
            broadcast_new_attack(attack_doc)
            broadcast_dashboard_update()
        logger.info(f"🎯 Scanner attack captured from {src_ip}: {cmd_str}")
    except Exception as e:
        logger.error(f"Failed to record HTTP probe: {e}")


def _register_socketio_events():
    """Import socketio_events module to register all Socket.IO handlers."""
    import app.socketio_events  # noqa: F401
    logger.info("Socket.IO event handlers registered")


def _seed_sample_data(app):
    """Seed sample Cowrie data on first run if database is empty."""
    from app.extensions import get_db
    from app.services.cowrie_service import parse_cowrie_logs
    from app.models.attack import create_attack
    from app.models.session import create_session
    from app.ai.stage_detector import detect_stage
    from app.ai.intent_detector import detect_intent
    from app.ai.persona_generator import generate_persona
    from app.services.threat_score_service import calculate_threat_score
    from app.services.mitre_service import map_commands
    
    db = get_db()
    
    # Only seed if attacks collection is empty
    if db.attacks.count_documents({}) > 0:
        logger.info("Database already has data, skipping seed")
        return
    
    log_path = app.config.get("COWRIE_LOG_PATH", "./app/data/sample_cowrie_logs.json")
    
    if not os.path.exists(log_path):
        logger.warning(f"Sample log file not found: {log_path}")
        return
    
    logger.info("Seeding database with sample Cowrie data...")
    
    sessions = parse_cowrie_logs(log_path)
    
    for session_data in sessions:
        commands = session_data.get("commands", [])
        duration = session_data.get("duration", 0)
        
        # Run AI analysis
        stage_result = detect_stage(commands)
        intent_result = detect_intent(commands)
        persona_result = generate_persona(commands, duration)
        
        score_data = {
            "commands": commands,
            "duration": duration,
            "attack_stage": stage_result["stage"],
            "intent": intent_result["intent"],
            "persona": persona_result,
            "downloaded_files": session_data.get("downloaded_files", []),
        }
        threat_result = calculate_threat_score(score_data)
        
        # Enrich session data with analysis
        session_data["attack_stage"] = stage_result["stage"]
        session_data["intent"] = intent_result["intent"]
        session_data["persona"] = persona_result
        session_data["threat_score"] = threat_result["score"]
        session_data["status"] = "analyzed"
        
        # Store in database
        create_attack(session_data)
        create_session(session_data)
        
        # Store analysis results in separate collections
        session_id = session_data["session_id"]
        from app.utils.helpers import utc_now
        
        db.attack_stages.update_one(
            {"session_id": session_id},
            {"$set": {**stage_result, "session_id": session_id, "detected_at": utc_now()}},
            upsert=True
        )
        db.intents.update_one(
            {"session_id": session_id},
            {"$set": {**intent_result, "session_id": session_id, "detected_at": utc_now()}},
            upsert=True
        )
        db.personas.update_one(
            {"session_id": session_id},
            {"$set": {**persona_result, "session_id": session_id, "generated_at": utc_now()}},
            upsert=True
        )
        db.threat_scores.update_one(
            {"session_id": session_id},
            {"$set": {**threat_result, "session_id": session_id, "calculated_at": utc_now()}},
            upsert=True
        )
    
    logger.info(f"✅ Seeded {len(sessions)} attack sessions with AI analysis")
