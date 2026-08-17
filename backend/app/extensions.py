"""
ShadowTrap AI X — Extensions Module
======================================
Initializes shared extensions (MongoDB, JWT, Socket.IO) as singletons
so they can be imported across the application.
"""

from pymongo import MongoClient
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

# ── MongoDB ──────────────────────────────────────────────
mongo_client = None
db = None


def init_mongodb(app):
    """Initialize MongoDB connection using app config."""
    global mongo_client, db
    mongo_uri = app.config.get("MONGO_URI", "mongodb://localhost:27017/shadowtrap")
    db_name = app.config.get("MONGO_DB_NAME", "shadowtrap")

    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[db_name]

    # Create indexes for performance
    _create_indexes()

    app.logger.info(f"MongoDB connected: {db_name}")
    return db


def _create_indexes():
    """Create database indexes for optimal query performance."""
    global db
    if db is None:
        return

    # ── Core Collections ──────────────────────────────────
    # Users
    db.users.create_index("email", unique=True)

    # Attacks
    db.attacks.create_index("session_id", unique=True)
    db.attacks.create_index("src_ip")
    db.attacks.create_index("created_at")
    db.attacks.create_index("threat_score")
    db.attacks.create_index("attack_stage")
    db.attacks.create_index("intent")
    db.attacks.create_index("is_live")

    # Sessions
    db.sessions.create_index("session_id", unique=True)
    db.sessions.create_index("src_ip")
    db.sessions.create_index("start_time")

    # ── AI Analysis Collections ───────────────────────────
    # Attack stages
    db.attack_stages.create_index("session_id")

    # Intents
    db.intents.create_index("session_id")

    # Predictions
    db.predictions.create_index("session_id")

    # Personas
    db.personas.create_index("session_id")

    # Threat scores
    db.threat_scores.create_index("session_id")

    # ── Behavior & Embeddings ─────────────────────────────
    # Behavior features
    db.behavior_features.create_index("session_id", unique=True)
    db.behavior_features.create_index("cluster_id")

    # Embeddings
    db.embeddings.create_index("session_id", unique=True)

    # ── Intelligence Collections ──────────────────────────
    # IP Intelligence
    db.ip_intelligence.create_index("ip", unique=True)
    db.ip_intelligence.create_index("country_code")

    # MITRE Mappings
    db.mitre_mappings.create_index("session_id")
    db.mitre_mappings.create_index("technique_id")

    # LLM Summaries
    db.llm_summaries.create_index("session_id")

    # ── Knowledge Graph ───────────────────────────────────
    db.knowledge_graph_nodes.create_index("node_id", unique=True)
    db.knowledge_graph_nodes.create_index("node_type")
    db.knowledge_graph_edges.create_index([("source", 1), ("target", 1)])
    db.knowledge_graph_edges.create_index("edge_type")

    # ── Reports ───────────────────────────────────────────
    db.reports.create_index("session_id")
    db.reports.create_index("generated_at")

    # ── AI Security Copilot Analyses ─────────────────────
    db.ai_analyses.create_index("session_id", unique=True)
    db.ai_analyses.create_index("src_ip")
    db.ai_analyses.create_index("analyzed_at")

    # ── Telegram Chats ───────────────────────────────────
    db.telegram_chats.create_index("chat_id", unique=True)

    # ── Self-Learning ─────────────────────────────────────
    db.learning_history.create_index("model_name")
    db.learning_history.create_index("trained_at")

    db.model_versions.create_index("model_name")
    db.model_versions.create_index([("model_name", 1), ("version", -1)])

    # ── Threat Intelligence ───────────────────────────────
    db.threat_intelligence.create_index("indicator")
    db.threat_intelligence.create_index("indicator_type")
    db.threat_intelligence.create_index("created_at")

    # ── Settings ──────────────────────────────────────────
    db.settings.create_index("key", unique=True)


def get_db():
    """Get the database instance. Raises error if not initialized."""
    global db
    if db is None:
        raise RuntimeError("Database not initialized. Call init_mongodb(app) first.")
    return db


# ── JWT ──────────────────────────────────────────────────
jwt = JWTManager()


def init_jwt(app):
    """Initialize JWT manager with the Flask app."""
    jwt.init_app(app)
    app.logger.info("JWT authentication initialized")
    return jwt


# ── Socket.IO ────────────────────────────────────────────
socketio = SocketIO()


def init_socketio(app):
    """
    Initialize Socket.IO with the Flask app.
    
    Uses eventlet for async support. Falls back to threading
    if eventlet is not available.
    """
    cors_origins = app.config.get("CORS_ORIGINS", ["*"])
    
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
        async_mode="eventlet",
        logger=False,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=25,
    )
    
    app.logger.info("Socket.IO initialized (async_mode=eventlet)")
    return socketio
