"""
ShadowTrap AI X — Similarity & Fingerprinting Engine
=====================================================
Generates behavioral fingerprints for attack sessions and computes
similarity against historical attacker profiles.
"""

import numpy as np

def generate_behavioral_fingerprint(commands, src_ip=""):
    """
    Generate unique behavioral hash/fingerprint of an attacker's session tactics.

    Args:
        commands: List of command strings
        src_ip: Attacker source IP

    Returns:
        dict: {
            "fingerprint_hash": str,
            "signature_vector": list of float,
            "command_pattern_summary": str
        }
    """
    import hashlib
    from app.ai.behavior_embedding import extract_behavioral_features

    features = extract_behavioral_features(commands)
    pattern_str = f"{features['has_download']}-{features['has_credential_access']}-{features['has_privilege_escalation']}-{features['has_persistence']}-{features['has_evasion']}"

    fingerprint_hash = hashlib.sha256(f"{pattern_str}-{len(commands)}-{src_ip}".encode()).hexdigest()[:16]

    summary = f"Pattern: {pattern_str} | Volume: {len(commands)} cmds"

    return {
        "fingerprint_hash": fingerprint_hash,
        "signature_vector": list(features.values()),
        "command_pattern_summary": summary
    }


def find_similar_attacks(session_id, limit=5):
    """
    Find top N most similar historical attack sessions based on behavior embeddings.

    Args:
        session_id: Target session ID
        limit: Number of matches to return

    Returns:
        list of {session_id, similarity_score, src_ip, stage, intent}
    """
    from app.extensions import get_db
    from app.ai.behavior_embedding import compute_similarity

    db = get_db()
    target_emb_doc = db.embeddings.find_one({"session_id": session_id})
    if not target_emb_doc or "embedding" not in target_emb_doc:
        return []

    target_emb = target_emb_doc["embedding"]

    all_embs = list(db.embeddings.find({"session_id": {"$ne": session_id}}))

    matches = []
    for doc in all_embs:
        other_sid = doc["session_id"]
        other_emb = doc.get("embedding", [])
        if not other_emb:
            continue

        sim = compute_similarity(target_emb, other_emb)
        if sim > 0.3:
            attack_doc = db.attacks.find_one({"session_id": other_sid}) or {}
            matches.append({
                "session_id": other_sid,
                "similarity_score": round(sim * 100, 1),
                "src_ip": attack_doc.get("src_ip", "Unknown"),
                "attack_stage": attack_doc.get("attack_stage", "Unknown"),
                "intent": attack_doc.get("intent", "Unknown"),
                "threat_score": attack_doc.get("threat_score", 0)
            })

    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    return matches[:limit]
