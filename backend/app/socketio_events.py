"""
ShadowTrap AI X — Socket.IO Event Handlers
=============================================
Real-time bidirectional communication layer for live
attack streaming, threat alerts, and dashboard updates.

Events Emitted (Server → Client):
    - new_attack          : New attack session detected
    - attack_update       : Existing session updated with new data
    - threat_alert        : High-severity threat notification
    - command_stream      : Live command from active session
    - analysis_complete   : AI analysis finished for a session
    - dashboard_update    : Aggregated stats refresh
    - model_update        : ML model training status

Events Received (Client → Server):
    - subscribe_session   : Client subscribes to a specific session
    - unsubscribe_session : Client unsubscribes from a session
    - request_analysis    : Client requests on-demand AI analysis
"""

from flask_socketio import emit, join_room, leave_room
from flask import request
from datetime import datetime
from app.extensions import socketio, get_db
from app.utils.logger import get_logger

logger = get_logger("socketio")

# Track connected clients
connected_clients = {}


@socketio.on("connect")
def handle_connect():
    """Handle new client connection."""
    client_id = request.sid
    connected_clients[client_id] = {
        "connected_at": datetime.utcnow().isoformat(),
        "subscribed_sessions": [],
    }
    
    # Send current stats on connect
    try:
        db = get_db()
        total = db.attacks.count_documents({})
        live = db.attacks.count_documents({"is_live": True})
        emit("dashboard_update", {
            "total_attacks": total,
            "live_sessions": live,
            "connected_clients": len(connected_clients),
        })
    except Exception:
        pass
    
    logger.info(f"Client connected: {client_id} (total: {len(connected_clients)})")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    client_id = request.sid
    connected_clients.pop(client_id, None)
    logger.info(f"Client disconnected: {client_id} (total: {len(connected_clients)})")


@socketio.on("subscribe_session")
def handle_subscribe_session(data):
    """
    Subscribe client to real-time updates for a specific session.
    
    Args:
        data: {"session_id": str}
    """
    session_id = data.get("session_id", "")
    if not session_id:
        return
    
    client_id = request.sid
    join_room(f"session_{session_id}")
    
    if client_id in connected_clients:
        connected_clients[client_id]["subscribed_sessions"].append(session_id)
    
    logger.debug(f"Client {client_id} subscribed to session: {session_id}")


@socketio.on("unsubscribe_session")
def handle_unsubscribe_session(data):
    """
    Unsubscribe client from a specific session's updates.
    
    Args:
        data: {"session_id": str}
    """
    session_id = data.get("session_id", "")
    if not session_id:
        return
    
    client_id = request.sid
    leave_room(f"session_{session_id}")
    
    if client_id in connected_clients:
        subs = connected_clients[client_id].get("subscribed_sessions", [])
        if session_id in subs:
            subs.remove(session_id)
    
    logger.debug(f"Client {client_id} unsubscribed from session: {session_id}")


@socketio.on("request_analysis")
def handle_request_analysis(data):
    """
    Client requests on-demand AI analysis for a session.
    
    Args:
        data: {"session_id": str}
    """
    session_id = data.get("session_id", "")
    if not session_id:
        emit("error", {"message": "session_id required"})
        return
    
    emit("analysis_status", {
        "session_id": session_id,
        "status": "queued",
        "message": "Analysis queued for processing",
    })
    
    logger.info(f"Analysis requested for session: {session_id}")


# ── Broadcast Helpers (called from services) ─────────────

def broadcast_new_attack(attack_data):
    """
    Broadcast new attack event to all connected clients.
    
    Args:
        attack_data: Serialized attack document dict
    """
    socketio.emit("new_attack", {
        "type": "new_attack",
        "data": attack_data,
    }, namespace="/")
    
    logger.info(f"Broadcast: new_attack session={attack_data.get('session_id', 'unknown')}")


def broadcast_attack_update(session_id, updates):
    """
    Broadcast attack update to subscribers of this session.
    
    Args:
        session_id: Session identifier
        updates: Dict of updated fields
    """
    socketio.emit("attack_update", {
        "type": "attack_update",
        "session_id": session_id,
        "data": updates,
    }, room=f"session_{session_id}", namespace="/")
    
    # Also broadcast to global feed
    socketio.emit("attack_update", {
        "type": "attack_update",
        "session_id": session_id,
        "data": updates,
    }, namespace="/")


def broadcast_threat_alert(alert_data):
    """
    Broadcast high-severity threat alert to all clients.
    
    Args:
        alert_data: Dict with alert details:
            - session_id: str
            - severity: str (critical, high, medium, low)
            - title: str
            - message: str
            - threat_score: int
    """
    socketio.emit("threat_alert", {
        "type": "threat_alert",
        "data": alert_data,
    }, namespace="/")
    
    logger.warning(f"Threat alert: {alert_data.get('severity', 'unknown')} - {alert_data.get('title', '')}")


def broadcast_command_stream(session_id, command_data):
    """
    Stream a live command from an active session.
    
    Args:
        session_id: Session identifier
        command_data: Dict with command details:
            - command: str
            - timestamp: str
            - index: int
    """
    socketio.emit("command_stream", {
        "type": "command_stream",
        "session_id": session_id,
        "data": command_data,
    }, room=f"session_{session_id}", namespace="/")


def broadcast_analysis_complete(session_id, analysis_data):
    """
    Notify clients that AI analysis is complete for a session.
    
    Args:
        session_id: Session identifier
        analysis_data: Dict with analysis results summary
    """
    socketio.emit("analysis_complete", {
        "type": "analysis_complete",
        "session_id": session_id,
        "data": analysis_data,
    }, room=f"session_{session_id}", namespace="/")
    
    # Also broadcast globally for dashboard updates
    socketio.emit("analysis_complete", {
        "type": "analysis_complete",
        "session_id": session_id,
        "data": analysis_data,
    }, namespace="/")


def broadcast_dashboard_update():
    """
    Broadcast aggregated dashboard stats update to all clients.
    Called after significant data changes.
    """
    try:
        db = get_db()
        total = db.attacks.count_documents({})
        live = db.attacks.count_documents({"is_live": True})
        high_risk = db.attacks.count_documents({"threat_score": {"$gte": 70}})
        
        pipeline = [
            {"$group": {"_id": None, "avg": {"$avg": "$threat_score"}}}
        ]
        avg_result = list(db.attacks.aggregate(pipeline))
        avg_score = round(avg_result[0]["avg"], 1) if avg_result else 0
        
        socketio.emit("dashboard_update", {
            "type": "dashboard_update",
            "data": {
                "total_attacks": total,
                "live_sessions": live,
                "high_risk_attacks": high_risk,
                "avg_threat_score": avg_score,
                "connected_clients": len(connected_clients),
            },
        }, namespace="/")
    except Exception as e:
        logger.error(f"Dashboard broadcast failed: {e}")


def broadcast_model_update(model_data):
    """
    Broadcast ML model training status update.
    
    Args:
        model_data: Dict with model training details:
            - model_name: str
            - status: str (training, completed, failed)
            - accuracy: float (if completed)
            - version: str
    """
    socketio.emit("model_update", {
        "type": "model_update",
        "data": model_data,
    }, namespace="/")
