"""
ShadowTrap AI X — Model Explainability (SHAP)
==============================================
Provides feature importance explanations using SHAP (SHapley Additive exPlanations)
for AI threat classification decisions.
"""

import numpy as np
from app.utils.logger import get_logger

logger = get_logger("ai.explainability")

FEATURE_NAMES = [
    "Total Commands", "Unique Commands", "Avg Command Length", "Max Command Length",
    "Download Activity", "Credential Access", "Privilege Escalation", "Persistence",
    "Defense Evasion", "Exfiltration", "Reconnaissance", "Command & Control",
    "Pipe Usage", "Redirection", "Sudo Count", "Unique Ratio"
]


def explain_threat_classification(commands):
    """
    Generate SHAP-based feature importance breakdown for threat classification.

    Args:
        commands: List of command strings

    Returns:
        dict: {
            "feature_importances": list of {feature, importance, impact},
            "summary": str,
            "method": str ("shap" or "tree_importance_fallback")
        }
    """
    if not commands:
        return {
            "feature_importances": [],
            "summary": "No commands provided for analysis.",
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

    # Try SHAP explainer
    shap_res = _try_shap_explanation(feature_vec)
    if shap_res is not None:
        return shap_res

    # Fallback importance calculation
    return _rule_importance_explanation(features)


def _try_shap_explanation(feature_vec):
    try:
        import shap
        import joblib
        import os

        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "models", "random_forest.joblib")
        if not os.path.exists(model_path):
            return None

        rf_model = joblib.load(model_path)
        explainer = shap.TreeExplainer(rf_model)
        shap_values = explainer.shap_values(feature_vec)

        # Handle multi-class output format
        if isinstance(shap_values, list):
            # Sum absolute shap values across classes
            vals = np.mean([np.abs(sv[0]) for sv in shap_values], axis=0)
        else:
            vals = np.abs(shap_values[0])

        importances = []
        for i, fname in enumerate(FEATURE_NAMES):
            imp_val = float(vals[i]) if i < len(vals) else 0.0
            importances.append({
                "feature": fname,
                "importance": round(imp_val, 4),
                "impact": "High" if imp_val > 0.1 else ("Medium" if imp_val > 0.03 else "Low")
            })

        importances.sort(key=lambda x: x["importance"], reverse=True)

        top_feats = ", ".join([f["feature"] for f in importances[:3]])
        summary = f"SHAP analysis identified '{top_feats}' as the primary drivers of this threat score."

        return {
            "feature_importances": importances,
            "summary": summary,
            "method": "shap"
        }
    except Exception as e:
        logger.warning(f"SHAP explanation failed: {e}")
        return None


def _rule_importance_explanation(features):
    """Rule-based feature contribution fallback."""
    contributions = [
        ("Credential Access", features["has_credential_access"] * 0.35),
        ("Privilege Escalation", features["has_privilege_escalation"] * 0.30),
        ("Download Activity", features["has_download"] * 0.25),
        ("Command & Control", features["has_c2"] * 0.25),
        ("Defense Evasion", features["has_evasion"] * 0.20),
        ("Persistence", features["has_persistence"] * 0.20),
        ("Exfiltration", features["has_exfiltration"] * 0.20),
        ("Reconnaissance", features["has_recon"] * 0.15),
        ("Sudo Count", features["sudo_count"] * 0.10),
        ("Command Volume", features["total_commands"] * 0.10)
    ]

    importances = []
    for fname, val in contributions:
        if val > 0:
            importances.append({
                "feature": fname,
                "importance": round(float(val), 4),
                "impact": "High" if val >= 0.25 else ("Medium" if val >= 0.15 else "Low")
            })

    importances.sort(key=lambda x: x["importance"], reverse=True)

    top_3 = [f["feature"] for f in importances[:3]]
    summary = f"Key contributing risk factors: {', '.join(top_3)}" if top_3 else "Standard baseline activity observed."

    return {
        "feature_importances": importances,
        "summary": summary,
        "method": "rule_based_contributions"
    }
