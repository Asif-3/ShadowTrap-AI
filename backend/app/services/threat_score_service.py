"""
ShadowTrap AI X — Threat Score Service
=========================================
Calculates composite threat scores combining rule-based heuristics,
ML anomaly detection, and command sequence trajectory risk.
"""

from app.utils.logger import get_logger

logger = get_logger("services.threat_score")


def calculate_threat_score(session_data):
    """
    Calculate dynamic multi-dimensional threat score (0 to 100).

    Args:
        session_data: Dict containing:
            - commands: list of str
            - duration: int (seconds)
            - attack_stage: str
            - intent: str
            - persona: dict
            - downloaded_files: list

    Returns:
        dict: {
            "score": int (0-100),
            "level": str ("Low", "Medium", "High", "Critical"),
            "breakdown": dict of sub-scores,
            "explainability": dict
        }
    """
    commands = session_data.get("commands", [])
    duration = session_data.get("duration", 0)
    stage = session_data.get("attack_stage", "Unknown")
    intent = session_data.get("intent", "Unknown")
    downloaded = session_data.get("downloaded_files", [])

    # 1. Base Stage Weight (Max 30)
    stage_weights = {
        "Reconnaissance": 10,
        "Discovery": 15,
        "Credential Discovery": 22,
        "Payload Download": 25,
        "Privilege Escalation": 28,
        "Persistence": 27,
        "Defense Evasion": 26,
        "Command And Control": 30,
        "Data Collection": 25,
        "Exfiltration": 30,
    }
    stage_score = stage_weights.get(stage, 10)

    # 2. Command Count & Obfuscation Score (Max 20)
    cmd_count = len(commands)
    cmd_score = min(15, cmd_count * 1.5)
    if any("base64" in c.lower() or "eval" in c.lower() for c in commands):
        cmd_score += 5
    cmd_score = min(20, cmd_score)

    # 3. Payload & File Risk (Max 20)
    payload_score = min(20, len(downloaded) * 10)

    # 4. ML Anomaly Score Integration (Max 15)
    try:
        from app.ai.anomaly_detector import detect_anomaly
        anomaly_res = detect_anomaly(commands)
        if anomaly_res.get("is_anomaly"):
            ml_anomaly_score = 15
        else:
            ml_anomaly_score = max(0, int((1.0 - anomaly_res.get("anomaly_score", 0.0)) * 7.5))
    except Exception:
        ml_anomaly_score = 5

    # 5. Sequence Trajectory Risk (Max 15)
    try:
        from app.ai.sequence_model import analyze_command_sequence
        seq_res = analyze_command_sequence(commands)
        seq_score = min(15, int(seq_res.get("trajectory_score", 0) * 0.15))
    except Exception:
        seq_score = 5

    # Total Score Calculation
    total_score = int(stage_score + cmd_score + payload_score + ml_anomaly_score + seq_score)
    total_score = min(100, max(0, total_score))

    if total_score >= 80:
        level = "Critical"
    elif total_score >= 60:
        level = "High"
    elif total_score >= 35:
        level = "Medium"
    else:
        level = "Low"

    # SHAP Explainability Generation
    try:
        from app.ai.explainability import explain_threat_classification
        exp_res = explain_threat_classification(commands)
    except Exception:
        exp_res = {"summary": "Standard activity profile.", "feature_importances": []}

    return {
        "score": total_score,
        "level": level,
        "breakdown": {
            "stage_risk": stage_score,
            "command_volatility": cmd_score,
            "payload_downloads": payload_score,
            "ml_anomaly_risk": ml_anomaly_score,
            "sequence_trajectory_risk": seq_score
        },
        "explainability": exp_res
    }
