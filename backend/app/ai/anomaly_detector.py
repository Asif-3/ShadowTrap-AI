"""
ShadowTrap AI X — Anomaly Detector
=====================================
Detects unknown/novel attack patterns using unsupervised
machine learning models:

    1. Isolation Forest — outlier detection
    2. DBSCAN — density-based clustering

These models identify attacks that don't match known patterns,
enabling zero-day and novel attack detection.
"""

import numpy as np
import joblib
import os
from app.utils.logger import get_logger

logger = get_logger("ai.anomaly")

# ── Model Storage ────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

_isolation_forest = None
_dbscan_model = None
_scaler = None


def _get_feature_vector(commands):
    """
    Convert commands into a feature vector for anomaly detection.
    
    Args:
        commands: List of command strings
        
    Returns:
        numpy array of shape (1, n_features)
    """
    from app.ai.behavior_embedding import extract_behavioral_features
    
    features = extract_behavioral_features(commands)
    
    vec = np.array([[
        features["total_commands"],
        features["unique_commands"],
        features["avg_command_length"],
        features["max_command_length"],
        features["has_download"],
        features["has_credential_access"],
        features["has_privilege_escalation"],
        features["has_persistence"],
        features["has_evasion"],
        features["has_exfiltration"],
        features["has_recon"],
        features["has_c2"],
        features["pipe_count"],
        features["redirect_count"],
        features["sudo_count"],
        features["unique_ratio"],
    ]])
    
    return vec


def detect_anomaly(commands):
    """
    Detect if an attack session is anomalous (novel/unknown pattern).
    
    Uses Isolation Forest for outlier detection. If the model hasn't
    been trained yet, uses heuristic-based anomaly scoring.
    
    Args:
        commands: List of command strings
        
    Returns:
        dict: {
            "is_anomaly": bool,
            "anomaly_score": float (-1.0 to 1.0, lower = more anomalous),
            "confidence": float (0-100),
            "cluster_id": int (-1 if no cluster assigned),
            "method": str
        }
    """
    if not commands:
        return {
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "confidence": 0.0,
            "cluster_id": -1,
            "method": "none",
        }
    
    feature_vec = _get_feature_vector(commands)
    
    # Try trained Isolation Forest
    global _isolation_forest
    if _isolation_forest is not None:
        try:
            score = _isolation_forest.decision_function(feature_vec)[0]
            prediction = _isolation_forest.predict(feature_vec)[0]
            
            return {
                "is_anomaly": prediction == -1,
                "anomaly_score": round(float(score), 4),
                "confidence": round(min(abs(score) * 100, 95.0), 1),
                "cluster_id": _assign_cluster(feature_vec),
                "method": "isolation_forest",
            }
        except Exception as e:
            logger.warning(f"Isolation Forest inference failed: {e}")
    
    # Try loading saved model
    model_path = os.path.join(MODEL_DIR, "isolation_forest.joblib")
    if os.path.exists(model_path):
        try:
            _isolation_forest = joblib.load(model_path)
            score = _isolation_forest.decision_function(feature_vec)[0]
            prediction = _isolation_forest.predict(feature_vec)[0]
            
            return {
                "is_anomaly": prediction == -1,
                "anomaly_score": round(float(score), 4),
                "confidence": round(min(abs(score) * 100, 95.0), 1),
                "cluster_id": _assign_cluster(feature_vec),
                "method": "isolation_forest",
            }
        except Exception as e:
            logger.warning(f"Failed to load Isolation Forest: {e}")
    
    # Fallback: heuristic anomaly detection
    return _heuristic_anomaly(commands, feature_vec)


def _heuristic_anomaly(commands, feature_vec):
    """
    Heuristic-based anomaly detection when ML model is unavailable.
    
    Flags sessions as anomalous if they exhibit unusual combinations
    of behaviors that don't match common attack patterns.
    """
    from app.ai.behavior_embedding import extract_behavioral_features
    features = extract_behavioral_features(commands)
    
    anomaly_indicators = 0
    total_checks = 10
    
    # Check for unusual patterns
    cmd_text = " ".join(commands).lower()
    
    # 1. Very long commands (obfuscation)
    if features["max_command_length"] > 0.7:
        anomaly_indicators += 1
    
    # 2. High pipe usage (complex chaining)
    if features["pipe_count"] > 0.5:
        anomaly_indicators += 1
    
    # 3. Base64 encoding (evasion)
    if "base64" in cmd_text:
        anomaly_indicators += 1
    
    # 4. Python/Perl one-liners (script injection)
    if any(k in cmd_text for k in ["python -c", "perl -e", "ruby -e"]):
        anomaly_indicators += 1
    
    # 5. Direct binary execution from /tmp
    if "/tmp/" in cmd_text and any(k in cmd_text for k in ["./", "chmod +x"]):
        anomaly_indicators += 1
    
    # 6. Multiple attack vectors in single session
    vectors = sum([
        features["has_download"],
        features["has_credential_access"],
        features["has_privilege_escalation"],
        features["has_persistence"],
        features["has_evasion"],
        features["has_c2"],
    ])
    if vectors >= 4:
        anomaly_indicators += 2
    
    # 7. Very low unique ratio (scripted/automated)
    if features["unique_ratio"] < 0.3 and features["total_commands"] > 0.2:
        anomaly_indicators += 1
    
    # 8. Unusual command patterns
    unusual = ["dd if=", "mkfifo", "/dev/tcp", "socat", "openssl s_client"]
    if any(k in cmd_text for k in unusual):
        anomaly_indicators += 1
    
    anomaly_score = max(-1.0, 1.0 - (anomaly_indicators / total_checks) * 2)
    is_anomaly = anomaly_indicators >= 3
    
    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": round(anomaly_score, 4),
        "confidence": round(min(anomaly_indicators * 15.0, 85.0), 1),
        "cluster_id": -1,
        "method": "heuristic",
    }


def _assign_cluster(feature_vec):
    """Assign a cluster ID using DBSCAN if available."""
    global _dbscan_model
    
    model_path = os.path.join(MODEL_DIR, "dbscan.joblib")
    if _dbscan_model is None and os.path.exists(model_path):
        try:
            _dbscan_model = joblib.load(model_path)
        except Exception:
            return -1
    
    if _dbscan_model is not None:
        try:
            # DBSCAN doesn't support predict, use nearest cluster center
            labels = _dbscan_model.labels_
            if hasattr(_dbscan_model, "components_") and len(_dbscan_model.components_) > 0:
                from sklearn.metrics.pairwise import euclidean_distances
                distances = euclidean_distances(feature_vec, _dbscan_model.components_)
                return int(labels[np.argmin(distances)])
        except Exception:
            pass
    
    return -1


def train_isolation_forest(all_features=None):
    """
    Train the Isolation Forest model on accumulated attack data.
    
    Args:
        all_features: Optional numpy array of feature vectors.
                      If None, fetches from database.
                      
    Returns:
        dict: Training results with model path and metrics
    """
    from sklearn.ensemble import IsolationForest
    global _isolation_forest
    
    if all_features is None:
        all_features = _fetch_training_features()
    
    if len(all_features) < 5:
        logger.warning("Not enough data to train Isolation Forest (need >= 5 samples)")
        return {"status": "insufficient_data", "samples": len(all_features)}
    
    logger.info(f"Training Isolation Forest on {len(all_features)} samples...")
    
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    
    model.fit(all_features)
    
    # Save model
    model_path = os.path.join(MODEL_DIR, "isolation_forest.joblib")
    joblib.dump(model, model_path)
    _isolation_forest = model
    
    # Calculate metrics
    scores = model.decision_function(all_features)
    predictions = model.predict(all_features)
    anomaly_count = int(np.sum(predictions == -1))
    
    logger.info(f"✅ Isolation Forest trained: {anomaly_count}/{len(all_features)} anomalies detected")
    
    return {
        "status": "trained",
        "model_path": model_path,
        "samples": len(all_features),
        "anomaly_count": anomaly_count,
        "avg_score": round(float(np.mean(scores)), 4),
    }


def train_dbscan(all_features=None):
    """
    Train DBSCAN clustering model on accumulated attack data.
    
    Args:
        all_features: Optional numpy array of feature vectors
        
    Returns:
        dict: Training results with cluster statistics
    """
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    global _dbscan_model, _scaler
    
    if all_features is None:
        all_features = _fetch_training_features()
    
    if len(all_features) < 3:
        logger.warning("Not enough data for DBSCAN clustering (need >= 3 samples)")
        return {"status": "insufficient_data", "samples": len(all_features)}
    
    logger.info(f"Training DBSCAN on {len(all_features)} samples...")
    
    # Scale features
    scaler = StandardScaler()
    scaled = scaler.fit_transform(all_features)
    
    model = DBSCAN(
        eps=0.5,
        min_samples=2,
        metric="euclidean",
        n_jobs=-1,
    )
    
    labels = model.fit_predict(scaled)
    
    # Save
    model_path = os.path.join(MODEL_DIR, "dbscan.joblib")
    scaler_path = os.path.join(MODEL_DIR, "dbscan_scaler.joblib")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    _dbscan_model = model
    _scaler = scaler
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_count = int(np.sum(labels == -1))
    
    logger.info(f"✅ DBSCAN trained: {n_clusters} clusters, {noise_count} noise points")
    
    return {
        "status": "trained",
        "model_path": model_path,
        "samples": len(all_features),
        "n_clusters": n_clusters,
        "noise_points": noise_count,
        "cluster_sizes": {
            str(label): int(np.sum(labels == label))
            for label in set(labels) if label != -1
        },
    }


def _fetch_training_features():
    """Fetch all attack feature vectors from the database."""
    try:
        from app.extensions import get_db
        db = get_db()
        
        attacks = list(db.attacks.find({}, {"commands": 1, "_id": 0}))
        
        features = []
        for attack in attacks:
            commands = attack.get("commands", [])
            if commands:
                vec = _get_feature_vector(commands)
                features.append(vec[0])
        
        return np.array(features) if features else np.array([])
    except Exception as e:
        logger.error(f"Failed to fetch training features: {e}")
        return np.array([])
