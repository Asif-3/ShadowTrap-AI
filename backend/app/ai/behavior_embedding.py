"""
ShadowTrap AI X — Behavior Embedding Engine
==============================================
Converts attacker command sequences into numerical vector
representations (embeddings) for similarity analysis,
clustering, and ML model input.

Methods:
    1. TF-IDF vectorization + Behavioral Features (lightweight, fast, 144 dims)
    2. Sentence Transformers (high-quality dense embeddings, cached)

The engine auto-selects the best available method.
"""

import numpy as np
from app.utils.logger import get_logger

logger = get_logger("ai.embedding")

# Global cached instances
_tfidf_vectorizer = None
_st_model = None
_st_checked = False
_st_available = False

# Reference corpus for consistent TF-IDF vocabulary across sessions
REFERENCE_PATTERNS = [
    "whoami id uname hostname w uptime env export",
    "cat /etc/passwd cat /etc/shadow cat /etc/group /etc/issue",
    "wget curl download http https ftp tftp fetch",
    "sudo su root privilege escalation chmod u+s chown",
    "crontab persistence systemctl service init.d bashrc profile",
    "history -c rm log evasion unset histfile clear",
    "nc netcat reverse shell bash -i /dev/tcp /dev/udp",
    "tar zip scp exfiltrate base64 gzip 7z",
    "nmap scan probe recon ping traceroute dig nslookup masscan",
    "ls dir find locate grep ps aux top htop",
]


def _get_tfidf_vectorizer():
    """Get or create the global pre-fitted TF-IDF vectorizer for consistent dimensions."""
    global _tfidf_vectorizer
    if _tfidf_vectorizer is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        _tfidf_vectorizer = TfidfVectorizer(
            max_features=128,
            ngram_range=(1, 2),
            analyzer="word",
            sublinear_tf=True,
        )
        _tfidf_vectorizer.fit(REFERENCE_PATTERNS)
    return _tfidf_vectorizer


def _try_sentence_transformers(text):
    """
    Attempt to use Sentence Transformers for high-quality embeddings.
    Model is lazy-loaded once and cached globally. If loading fails,
    subsequent calls immediately return None without delay.
    
    Returns:
        numpy array or None if unavailable
    """
    global _st_model, _st_checked, _st_available
    
    if not _st_checked:
        _st_checked = True
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
            _st_available = True
            logger.info("SentenceTransformer model successfully loaded.")
        except Exception as e:
            _st_available = False
            _st_model = None
            logger.info(f"SentenceTransformer unavailable, falling back to TF-IDF: {e}")
            
    if not _st_available or _st_model is None:
        return None
        
    try:
        embedding = _st_model.encode(text, convert_to_numpy=True)
        return embedding
    except Exception as e:
        logger.warning(f"SentenceTransformer encode failed: {e}")
        return None


def generate_embedding(commands, method="auto"):
    """
    Generate a numerical embedding vector from a command sequence.
    
    Args:
        commands: List of command strings (or single string command)
        method: "auto", "tfidf", or "transformer"
        
    Returns:
        dict: {
            "embedding": list of floats,
            "method": str,
            "dimensions": int
        }
    """
    cleaned_commands = _sanitize_commands(commands)
    
    if not cleaned_commands:
        return {
            "embedding": [0.0] * 144,
            "method": "zero",
            "dimensions": 144,
        }
    
    text = " ; ".join(cleaned_commands)
    
    # Try Sentence Transformers first if requested/auto
    if method in ("auto", "transformer"):
        st_embedding = _try_sentence_transformers(text)
        if st_embedding is not None:
            return {
                "embedding": st_embedding.tolist(),
                "method": "sentence_transformer",
                "dimensions": len(st_embedding),
            }
    
    # Fallback to TF-IDF + Behavioral Features
    return _generate_tfidf_embedding(cleaned_commands)


def _sanitize_commands(commands):
    """Ensure commands is a clean list of non-empty strings."""
    if commands is None:
        return []
    if isinstance(commands, str):
        commands = [commands]
    if not isinstance(commands, (list, tuple)):
        return []
    
    cleaned = []
    for cmd in commands:
        if cmd is not None:
            cmd_str = str(cmd).strip()
            if cmd_str:
                cleaned.append(cmd_str)
    return cleaned


def _generate_tfidf_embedding(commands):
    """
    Generate TF-IDF based embedding with feature engineering.
    
    Combines TF-IDF vectors (128 features) with hand-crafted behavioral
    features (16 features) for a rich, deterministic representation (144 dims).
    """
    cleaned_commands = _sanitize_commands(commands)
    if not cleaned_commands:
        return {
            "embedding": [0.0] * 144,
            "method": "zero",
            "dimensions": 144,
        }
        
    text = " ".join(cleaned_commands)
    
    try:
        vectorizer = _get_tfidf_vectorizer()
        raw_vec = vectorizer.transform([text]).toarray().flatten()
        tfidf_vec = np.zeros(128, dtype=np.float64)
        tfidf_vec[:min(len(raw_vec), 128)] = raw_vec[:128]
    except Exception as e:
        logger.warning(f"TF-IDF transform failed: {e}")
        tfidf_vec = np.zeros(128, dtype=np.float64)
    
    # Add behavioral features (16 features)
    behavioral = extract_behavioral_features(cleaned_commands)
    behavioral_vec = np.array([
        behavioral["total_commands"],
        behavioral["unique_commands"],
        behavioral["avg_command_length"],
        behavioral["max_command_length"],
        behavioral["has_download"],
        behavioral["has_credential_access"],
        behavioral["has_privilege_escalation"],
        behavioral["has_persistence"],
        behavioral["has_evasion"],
        behavioral["has_exfiltration"],
        behavioral["has_recon"],
        behavioral["has_c2"],
        behavioral["pipe_count"],
        behavioral["redirect_count"],
        behavioral["sudo_count"],
        behavioral["unique_ratio"],
    ], dtype=np.float64)
    
    # Combine (128 TF-IDF + 16 behavioral = 144 dims)
    combined = np.concatenate([tfidf_vec[:128], behavioral_vec])
    
    # L2 normalize
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm
    
    return {
        "embedding": combined.tolist(),
        "method": "tfidf_behavioral",
        "dimensions": len(combined),
    }


def extract_behavioral_features(commands):
    """
    Extract hand-crafted behavioral features from command sequences.
    
    Args:
        commands: List of command strings (or single string command)
        
    Returns:
        dict: Feature name to value mapping
    """
    cleaned_commands = _sanitize_commands(commands)
    
    default_features = {k: 0.0 for k in [
        "total_commands", "unique_commands", "avg_command_length",
        "max_command_length", "has_download", "has_credential_access",
        "has_privilege_escalation", "has_persistence", "has_evasion",
        "has_exfiltration", "has_recon", "has_c2", "pipe_count",
        "redirect_count", "sudo_count", "unique_ratio",
    ]}
    
    if not cleaned_commands:
        return default_features
    
    cmd_text = " ".join(cleaned_commands).lower()
    
    total = len(cleaned_commands)
    unique = len(set(cleaned_commands))
    lengths = [len(c) for c in cleaned_commands]
    
    return {
        "total_commands": float(min(total / 50.0, 1.0)),  # Normalized
        "unique_commands": float(min(unique / 30.0, 1.0)),
        "avg_command_length": float(min(float(np.mean(lengths)) / 100.0, 1.0)),
        "max_command_length": float(min(float(max(lengths)) / 200.0, 1.0)),
        "has_download": float(any(k in cmd_text for k in ["wget", "curl", "fetch", "download"])),
        "has_credential_access": float(any(k in cmd_text for k in ["/etc/passwd", "/etc/shadow", "credentials", "password", ".ssh"])),
        "has_privilege_escalation": float(any(k in cmd_text for k in ["sudo", "su -", "su root", "chmod u+s", "suid"])),
        "has_persistence": float(any(k in cmd_text for k in ["crontab", "systemctl enable", "rc.local", "useradd", ".bashrc"])),
        "has_evasion": float(any(k in cmd_text for k in ["history -c", "rm -rf /var/log", "iptables -f", "unset histfile"])),
        "has_exfiltration": float(any(k in cmd_text for k in ["scp ", "sftp ", "curl -x post", "base64", "nc "])),
        "has_recon": float(any(k in cmd_text for k in ["nmap", "masscan", "ping", "traceroute", "dig"])),
        "has_c2": float(any(k in cmd_text for k in ["nc -", "netcat", "reverse", "/dev/tcp", "bash -i"])),
        "pipe_count": float(min(cmd_text.count("|") / 10.0, 1.0)),
        "redirect_count": float(min((cmd_text.count(">") + cmd_text.count(">>")) / 5.0, 1.0)),
        "sudo_count": float(min(cmd_text.count("sudo") / 5.0, 1.0)),
        "unique_ratio": float(unique / max(total, 1)),
    }


def compute_similarity(embedding_a, embedding_b):
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        embedding_a: First embedding vector (list of floats)
        embedding_b: Second embedding vector (list of floats)
        
    Returns:
        float: Cosine similarity score (0.0 to 1.0)
    """
    if not embedding_a or not embedding_b:
        return 0.0
        
    try:
        a = np.array(embedding_a, dtype=np.float64).flatten()
        b = np.array(embedding_b, dtype=np.float64).flatten()
        
        if len(a) == 0 or len(b) == 0:
            return 0.0
            
        # Check for NaN / Inf
        if np.isnan(a).any() or np.isnan(b).any() or np.isinf(a).any() or np.isinf(b).any():
            return 0.0
            
        # Pad shorter vector if necessary
        max_len = max(len(a), len(b))
        if len(a) < max_len:
            a = np.pad(a, (0, max_len - len(a)))
        if len(b) < max_len:
            b = np.pad(b, (0, max_len - len(b)))
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = float(dot_product / (norm_a * norm_b))
        
        if np.isnan(similarity) or np.isinf(similarity):
            return 0.0
            
        # Clip to valid cosine similarity range [0.0, 1.0]
        return float(np.clip(similarity, 0.0, 1.0))
    except Exception as e:
        logger.warning(f"Error computing similarity: {e}")
        return 0.0
