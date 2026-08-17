"""
ShadowTrap AI - Next Attack Predictor
========================================
Predicts the most likely next attack stage using a
Markov chain transition probability matrix.
"""

from app.utils.logger import get_logger

logger = get_logger("ai.predictor")

# ── Markov Chain Transition Matrix ───────────────────────
# Based on real-world attack chain analysis
# probability[current_stage] = {next_stage: probability}
TRANSITION_MATRIX = {
    "Reconnaissance": {
        "Discovery": 0.45,
        "Credential Discovery": 0.25,
        "Payload Download": 0.15,
        "Privilege Escalation": 0.05,
        "Persistence": 0.03,
        "Defense Evasion": 0.02,
        "Command And Control": 0.03,
        "Data Collection": 0.01,
        "Exfiltration": 0.01,
    },
    "Discovery": {
        "Credential Discovery": 0.35,
        "Payload Download": 0.20,
        "Privilege Escalation": 0.15,
        "Reconnaissance": 0.10,
        "Persistence": 0.05,
        "Defense Evasion": 0.05,
        "Data Collection": 0.05,
        "Command And Control": 0.03,
        "Exfiltration": 0.02,
    },
    "Credential Discovery": {
        "Privilege Escalation": 0.30,
        "Payload Download": 0.25,
        "Data Collection": 0.15,
        "Persistence": 0.10,
        "Defense Evasion": 0.08,
        "Discovery": 0.05,
        "Exfiltration": 0.04,
        "Command And Control": 0.02,
        "Reconnaissance": 0.01,
    },
    "Payload Download": {
        "Privilege Escalation": 0.30,
        "Persistence": 0.25,
        "Command And Control": 0.20,
        "Defense Evasion": 0.10,
        "Data Collection": 0.05,
        "Discovery": 0.05,
        "Exfiltration": 0.03,
        "Credential Discovery": 0.01,
        "Reconnaissance": 0.01,
    },
    "Privilege Escalation": {
        "Persistence": 0.30,
        "Data Collection": 0.20,
        "Defense Evasion": 0.15,
        "Payload Download": 0.10,
        "Credential Discovery": 0.10,
        "Command And Control": 0.08,
        "Exfiltration": 0.04,
        "Discovery": 0.02,
        "Reconnaissance": 0.01,
    },
    "Persistence": {
        "Defense Evasion": 0.30,
        "Data Collection": 0.25,
        "Command And Control": 0.15,
        "Privilege Escalation": 0.10,
        "Exfiltration": 0.08,
        "Payload Download": 0.05,
        "Discovery": 0.04,
        "Credential Discovery": 0.02,
        "Reconnaissance": 0.01,
    },
    "Defense Evasion": {
        "Data Collection": 0.25,
        "Command And Control": 0.20,
        "Persistence": 0.15,
        "Exfiltration": 0.15,
        "Payload Download": 0.10,
        "Privilege Escalation": 0.05,
        "Discovery": 0.05,
        "Credential Discovery": 0.03,
        "Reconnaissance": 0.02,
    },
    "Command And Control": {
        "Data Collection": 0.30,
        "Exfiltration": 0.25,
        "Persistence": 0.15,
        "Defense Evasion": 0.10,
        "Payload Download": 0.10,
        "Privilege Escalation": 0.05,
        "Discovery": 0.03,
        "Credential Discovery": 0.01,
        "Reconnaissance": 0.01,
    },
    "Data Collection": {
        "Exfiltration": 0.50,
        "Defense Evasion": 0.15,
        "Command And Control": 0.10,
        "Persistence": 0.10,
        "Data Collection": 0.05,
        "Privilege Escalation": 0.04,
        "Discovery": 0.03,
        "Payload Download": 0.02,
        "Reconnaissance": 0.01,
    },
    "Exfiltration": {
        "Defense Evasion": 0.35,
        "Persistence": 0.20,
        "Data Collection": 0.15,
        "Command And Control": 0.10,
        "Exfiltration": 0.10,
        "Discovery": 0.04,
        "Payload Download": 0.03,
        "Privilege Escalation": 0.02,
        "Reconnaissance": 0.01,
    },
}


def predict_next_stage(current_stage):
    """
    Predict the most likely next attack stage.
    
    Uses a Markov chain transition probability matrix
    trained on real-world attack chain data.
    
    Args:
        current_stage: Current detected attack stage string
        
    Returns:
        dict: {
            "current_stage": str,
            "predicted_stage": str,
            "confidence": float (0-100),
            "all_predictions": list of {stage, probability},
            "transition_chain": list of likely 3-step chain
        }
    """
    if current_stage not in TRANSITION_MATRIX:
        return {
            "current_stage": current_stage,
            "predicted_stage": "Discovery",
            "confidence": 20.0,
            "all_predictions": [],
            "transition_chain": [],
        }
    
    transitions = TRANSITION_MATRIX[current_stage]
    
    # Sort by probability (descending)
    sorted_transitions = sorted(
        transitions.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    all_predictions = [
        {
            "stage": stage,
            "probability": round(prob * 100, 1),
        }
        for stage, prob in sorted_transitions
    ]
    
    # Primary prediction
    predicted_stage = sorted_transitions[0][0]
    confidence = round(sorted_transitions[0][1] * 100, 1)
    
    # Build 3-step prediction chain
    chain = [current_stage]
    next_stage = predicted_stage
    for _ in range(2):
        chain.append(next_stage)
        if next_stage in TRANSITION_MATRIX:
            next_transitions = TRANSITION_MATRIX[next_stage]
            next_stage = max(next_transitions, key=next_transitions.get)
        else:
            break
    
    return {
        "current_stage": current_stage,
        "predicted_stage": predicted_stage,
        "confidence": confidence,
        "all_predictions": all_predictions,
        "transition_chain": chain,
    }
