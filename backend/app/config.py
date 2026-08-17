"""
ShadowTrap AI - Configuration Module
=====================================
Loads environment variables and provides configuration classes
for different deployment environments.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "shadowtrap-fallback-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT = int(os.getenv("FLASK_PORT", 5000))

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/shadowtrap")
    MONGO_DB_NAME = "shadowtrap"

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "shadowtrap-fallback-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 86400))
    )
    JWT_TOKEN_LOCATION = ["headers", "query_string"]
    JWT_QUERY_STRING_NAME = "token"
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # ── Local LLM (llama.cpp + Qwen3-0.6B) ──────────────────
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "llama_cpp")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "Qwen3-0.6B-Q4_K_M")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 60))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.2))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 512))
    LLM_CONTEXT_SIZE = int(os.getenv("LLM_CONTEXT_SIZE", 4096))

    # AI Alert Threshold — minimum threat score to trigger AI analysis + Telegram
    AI_ALERT_THRESHOLD = int(os.getenv("AI_ALERT_THRESHOLD", 60))

    # ── Telegram ─────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # Cowrie
    COWRIE_LOG_PATH = os.getenv(
        "COWRIE_LOG_PATH", "./app/data/sample_cowrie_logs.json"
    )

    # Report Storage
    REPORT_STORAGE_PATH = os.getenv("REPORT_STORAGE_PATH", "./reports")

    # Admin Default Credentials
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@shadowtrap.ai")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ShadowTrap@2024")

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration map
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    """Get the appropriate configuration based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
