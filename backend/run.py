"""
ShadowTrap AI X — Flask Application Entry Point
===================================================
Run this file to start the backend API server with
Socket.IO support for real-time streaming.

Usage:
    python run.py
"""

import os
import sys

# Ensure UTF-8 output encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import socketio

app = create_app()


if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    use_reloader = False
    
    # Ensure background services initialize when reloader is disabled or in child worker
    is_main_worker = not use_reloader or os.getenv("WERKZEUG_RUN_MAIN") == "true"
    
    if is_main_worker:
        print(f"[STARTUP] ShadowTrap backend starting on {host}:{port}")
        
        # Start background Network Scan Detector with existing app instance
        try:
            import threading
            from scan_detector import ScanDetector
            def _run_detector():
                try:
                    detector = ScanDetector(app)
                    detector.start()
                except Exception as e:
                    print(f"[WORKER] Scan detector notice: {e}")
            t = threading.Thread(target=_run_detector, daemon=True)
            t.start()
        except Exception as e:
            print(f"[WORKER] Network scan detector initialization error: {e}")

        # Check Local LLM (llama.cpp + Qwen3-0.6B) health
        try:
            from app.services.llm_service import check_llm_health
            health = check_llm_health()
            if health["available"]:
                print(f"[LLM] llama.cpp health: OK ({health['model']} at {health['endpoint']})")
            else:
                print(f"[LLM] Service unavailable: {health['error']}")
        except Exception as e:
            print(f"[LLM] Health check error: {e}")

        # Start Telegram Bot
        try:
            from app.services.telegram_service import start_telegram_bot
            start_telegram_bot(app)
            print(f"[TELEGRAM] Telegram service initialized")
        except Exception as e:
            print(f"[TELEGRAM] Initialization error: {e}")

    # Use socketio.run() for WebSocket & HTTP server
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=False,
        log_output=True,
    )
