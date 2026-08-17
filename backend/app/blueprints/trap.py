"""
ShadowTrap AI — Trap Logging Blueprint
=======================================
Silent endpoint that receives fingerprint and behavioral data
from the decoy website. Stores everything in MongoDB for analysis.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from app.utils.logger import get_logger

logger = get_logger("trap")

trap_bp = Blueprint("trap", __name__, url_prefix="/api/trap")


@trap_bp.route("/log", methods=["POST"])
def log_trap_event():
    """
    Silently receive and store visitor telemetry from the decoy page.
    No authentication required — this must be open for attackers to hit.
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Enrich with server-side data
        trap_event = {
            "visitor_ip": request.remote_addr,
            "forwarded_for": request.headers.get("X-Forwarded-For", ""),
            "user_agent": request.headers.get("User-Agent", ""),
            "referer": request.headers.get("Referer", ""),
            "accept_language": request.headers.get("Accept-Language", ""),
            "event_type": data.get("type", "unknown"),
            "client_data": data,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "request_method": request.method,
            "content_length": request.content_length,
        }
        
        # Store in MongoDB
        from app.extensions import get_db
        db = get_db()
        db.trap_visitors.insert_one(trap_event)
        
        logger.info(
            f"🕸️  Trap event [{data.get('type', 'unknown')}] from "
            f"{request.remote_addr} — UA: {request.headers.get('User-Agent', 'N/A')[:60]}"
        )
        
        # Return innocuous response (looks like an analytics pixel)
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        logger.error(f"Trap log error: {e}")
        # Still return 200 to avoid suspicion
        return jsonify({"status": "ok"}), 200


@trap_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login_trap():
    """
    Decoy Admin Login Endpoint — Handles Hydra & browser brute-force login attempts.
    Captures attacker IP, user-agent, username & password guesses.
    If weak password is provided, returns SUCCESS so attacker accesses fake admin dashboard,
    while recording full breach metrics to the real SOC Admin Panel!
    """
    from flask import request
    from app.extensions import get_db
    from app.models.attack import create_attack
    from app.ai.stage_detector import detect_stage
    from app.ai.intent_detector import detect_intent
    from app.services.threat_score_service import calculate_threat_score
    from app.socketio_events import (
        broadcast_new_attack, broadcast_attack_update,
        broadcast_dashboard_update, broadcast_threat_alert
    )
    from app.utils.helpers import utc_now

    if request.method == "GET":
        return jsonify({
            "status": "ok",
            "service": "TechNova Corporate Admin Portal",
            "auth_method": "POST username/password"
        }), 200

    # Parse form or JSON parameters (supports Hydra http-post-form format)
    req_data = request.get_json(silent=True) or {}
    username = (
        request.form.get("username") or request.form.get("user") or
        request.form.get("login") or req_data.get("username") or
        req_data.get("user") or request.args.get("username") or "admin"
    ).strip()

    password = (
        request.form.get("password") or request.form.get("pass") or
        request.form.get("pwd") or req_data.get("password") or
        req_data.get("pass") or request.args.get("password") or ""
    ).strip()

    src_ip = request.remote_addr or "127.0.0.1"
    user_agent = request.headers.get("User-Agent", "Hydra / HTTP Client")

    # Check if weak credential matched decoy trap list
    WEAK_USERNAMES = ["admin", "administrator", "root", "sysadmin", "user", "manager"]
    WEAK_PASSWORDS = ["admin", "admin123", "password", "password123", "123456", "secret", "root", "shadowtrap", "12345", "pass123"]

    is_success = (username.lower() in WEAK_USERNAMES) and (password in WEAK_PASSWORDS)

    # 1. Store in trap_visitors collection
    db = get_db()
    trap_doc = {
        "visitor_ip": src_ip,
        "forwarded_for": request.headers.get("X-Forwarded-For", ""),
        "user_agent": user_agent,
        "event_type": "form_submission",
        "client_data": {
            "type": "admin_login_attempt",
            "username": username,
            "password": password,
            "is_success": is_success,
        },
        "received_at": utc_now().isoformat(),
        "request_method": "POST",
    }
    db.trap_visitors.insert_one(trap_doc)

    # 2. Store or update Attack Session in db.attacks
    session_id = f"HYDRA-{src_ip.replace('.', '')}"
    now = utc_now()
    result_str = "CRACKED / GRANTED" if is_success else "FAILED"
    cmd_str = f"Hydra/Form Attempt: user='{username}' pass='{password}' -> {result_str}"

    existing = db.attacks.find_one({"session_id": session_id})

    if existing:
        commands = existing.get("commands", [])
        if cmd_str not in commands:
            commands.append(cmd_str)
        timestamps = existing.get("timestamps", [])
        timestamps.append(now.isoformat())

        stage_name = "Initial Access" if is_success else "Credential Access"
        intent_name = "System Compromise / Cracked Password" if is_success else "Hydra Brute-Force / Credential Theft"
        new_score = 98 if is_success else max(existing.get("threat_score", 0), 75)

        db.attacks.update_one(
            {"session_id": session_id},
            {"$set": {
                "commands": commands,
                "command_count": len(commands),
                "timestamps": timestamps,
                "attack_stage": stage_name,
                "intent": intent_name,
                "threat_score": new_score,
                "status": "analyzed",
                "is_live": True,
                "persona": {
                    "skill_level": "Automated Tool (Hydra)",
                    "attack_style": "HTTP Form Brute-Force",
                    "cracked_username": username if is_success else "",
                    "cracked_password": password if is_success else "",
                },
                "updated_at": now,
            }}
        )

        broadcast_attack_update(session_id, {
            "commands": commands,
            "command_count": len(commands),
            "threat_score": new_score,
            "attack_stage": stage_name,
            "intent": intent_name,
            "is_live": True,
        })
        broadcast_dashboard_update()

    else:
        commands = [cmd_str]
        stage_name = "Initial Access" if is_success else "Credential Access"
        intent_name = "System Compromise / Cracked Password" if is_success else "Hydra Brute-Force / Credential Theft"
        new_score = 98 if is_success else 75

        attack_doc = {
            "session_id": session_id,
            "src_ip": src_ip,
            "src_port": request.environ.get("REMOTE_PORT", 0),
            "dst_port": 5000,
            "protocol": "HTTP-POST",
            "username": username,
            "password": password,
            "commands": commands,
            "timestamps": [now.isoformat()],
            "downloaded_files": [],
            "executed_files": [],
            "start_time": now,
            "duration": 1,
            "command_count": 1,
            "status": "analyzed",
            "threat_score": new_score,
            "attack_stage": stage_name,
            "intent": intent_name,
            "persona": {
                "skill_level": "Automated Tool (Hydra)",
                "attack_style": "HTTP Form Brute-Force",
                "cracked_username": username if is_success else "",
                "cracked_password": password if is_success else "",
            },
            "is_live": True,
            "created_at": now,
            "updated_at": now,
        }
        create_attack(attack_doc)
        broadcast_new_attack(attack_doc)
        broadcast_dashboard_update()

    # If password cracked successfully, issue high priority alert
    if is_success:
        broadcast_threat_alert({
            "session_id": session_id,
            "severity": "CRITICAL",
            "title": f"🚨 HYDRA BRUTE-FORCE SUCCESS: Password Cracked ('{password}')",
            "message": f"Attacker from IP {src_ip} successfully cracked credentials: user='{username}', pass='{password}'",
            "threat_score": 98,
        })

    logger.info(f"🔑 Decoy login attempt from {src_ip}: user='{username}' pass='{password}' -> Success={is_success}")

    if is_success:
        return jsonify({
            "status": "success",
            "success": True,
            "message": "Login successful. Welcome to TechNova Enterprise Control Console.",
            "token": "decoy_admin_session_token_991823",
            "redirect": "/decoy-admin-dashboard"
        }), 200

    return jsonify({
        "status": "error",
        "success": False,
        "error": "Invalid credentials. Unauthorized access attempt logged.",
        "message": "Invalid username or password"
    }), 401


@trap_bp.route("/visitors", methods=["GET"])
def get_trap_visitors():
    """
    Protected endpoint — returns all captured trap visitor data.
    Used by the SOC dashboard's TrapVisitors page.
    Requires JWT authentication (enforced by the DashboardLayout).
    """
    from flask_jwt_extended import jwt_required
    
    @jwt_required()
    def _inner():
        from app.extensions import get_db
        db = get_db()
        
        # Get all visitors, most recent first
        visitors = list(
            db.trap_visitors.find(
                {},
                {"_id": 0}
            ).sort("received_at", -1).limit(200)
        )
        
        # Build summary stats
        total_events = db.trap_visitors.count_documents({})
        unique_ips = len(db.trap_visitors.distinct("visitor_ip"))
        fingerprints = db.trap_visitors.count_documents({"event_type": "fingerprint"})
        devtools_detected = db.trap_visitors.count_documents({"event_type": "devtools_detected"})
        form_submissions = db.trap_visitors.count_documents({"event_type": "form_submission"})
        
        return jsonify({
            "success": True,
            "data": {
                "visitors": visitors,
                "stats": {
                    "total_events": total_events,
                    "unique_ips": unique_ips,
                    "fingerprints": fingerprints,
                    "devtools_detected": devtools_detected,
                    "form_submissions": form_submissions,
                }
            }
        }), 200
    
    return _inner()
