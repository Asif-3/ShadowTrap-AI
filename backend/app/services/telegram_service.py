"""
ShadowTrap AI - Telegram Notification Service
================================================
Sends security alerts to Telegram with:
    - Static TELEGRAM_CHAT_ID support
    - Dynamic chat registration via /start
    - AI Security Copilot analysis in alerts
    - HTML escaping for attacker-controlled data
    - Retry with exponential backoff
    - Rate limiting (20 msg/min per chat)
    - Duplicate alert prevention
    - Message length protection (4096 char limit)
    - Structured logging
    - Graceful failure — never crashes the main app
"""

import os
import time
import html
import threading
import requests
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from app.extensions import get_db
from app.utils.logger import get_logger
from app.config import Config

# Define IST timezone (UTC+5:30)
ist_tz = timezone(timedelta(hours=5, minutes=30))

logger = get_logger("services.telegram")

TELEGRAM_API_URL = "https://api.telegram.org/bot"
TELEGRAM_MAX_MSG_LEN = 4096
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1  # seconds, exponential backoff
RATE_LIMIT_PER_MIN = 20
ALERT_COOLDOWN_SECONDS = 300  # 5 minutes between duplicate alerts for same session

# Rate limiting state
_rate_tracker = defaultdict(list)  # chat_id -> list of timestamps
_rate_lock = threading.Lock()

# Deduplication state
_sent_alerts = {}  # session_id -> last_sent_timestamp
_dedup_lock = threading.Lock()


# ─── Token / Chat ID Helpers ──────────────────────────────

def _get_bot_token():
    """Get Telegram bot token from config."""
    return Config.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")


def _get_all_chat_ids():
    """
    Get all chat IDs to send alerts to.
    Combines static TELEGRAM_CHAT_ID with dynamically registered chats.
    """
    chat_ids = set()
    
    # Static chat ID from config
    static_id = Config.TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "")
    if static_id:
        try:
            chat_ids.add(int(static_id))
        except (ValueError, TypeError):
            logger.warning(f"Invalid TELEGRAM_CHAT_ID: {static_id}")
    
    # Dynamically registered chats from database
    try:
        db = get_db()
        for chat in db.telegram_chats.find({}, {"chat_id": 1}):
            cid = chat.get("chat_id")
            if cid:
                chat_ids.add(int(cid))
    except Exception as e:
        logger.debug(f"Could not fetch registered chats: {e}")
    
    return list(chat_ids)


# ─── HTML Escaping ────────────────────────────────────────

def _escape(text):
    """Escape text for Telegram HTML parse mode. Prevents injection."""
    if not text:
        return ""
    return html.escape(str(text))


# ─── Rate Limiting ────────────────────────────────────────

def _check_rate_limit(chat_id):
    """Check if we can send to this chat without exceeding rate limit."""
    now = time.time()
    with _rate_lock:
        # Clean old entries (older than 60 seconds)
        _rate_tracker[chat_id] = [
            ts for ts in _rate_tracker[chat_id] if now - ts < 60
        ]
        if len(_rate_tracker[chat_id]) >= RATE_LIMIT_PER_MIN:
            return False
        _rate_tracker[chat_id].append(now)
        return True


# ─── Deduplication ────────────────────────────────────────

def _is_duplicate_alert(session_id):
    """Check if we recently sent an alert for this session."""
    now = time.time()
    with _dedup_lock:
        last_sent = _sent_alerts.get(session_id, 0)
        if now - last_sent < ALERT_COOLDOWN_SECONDS:
            return True
        _sent_alerts[session_id] = now
        # Clean old entries
        expired = [sid for sid, ts in _sent_alerts.items() if now - ts > ALERT_COOLDOWN_SECONDS * 2]
        for sid in expired:
            del _sent_alerts[sid]
        return False


# ─── Core Message Sender ─────────────────────────────────

def _send_message(token, chat_id, text, retries=MAX_RETRIES):
    """
    Send a message to a Telegram chat with retry and backoff.
    
    Returns:
        bool: True if sent successfully
    """
    if not token or not chat_id:
        return False
    
    # Truncate to Telegram limit
    if len(text) > TELEGRAM_MAX_MSG_LEN:
        text = text[:TELEGRAM_MAX_MSG_LEN - 20] + "\n\n... (truncated)"
    
    url = f"{TELEGRAM_API_URL}{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=5)
            
            if resp.status_code == 200:
                return True
            
            # Rate limited by Telegram
            if resp.status_code == 429:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
                logger.warning(f"Telegram rate limited, waiting {retry_after}s")
                if attempt < retries:
                    time.sleep(retry_after)
                    continue
                    
            # Other errors
            logger.warning(
                f"Telegram send failed (attempt {attempt}/{retries}): "
                f"HTTP {resp.status_code} — {resp.text[:200]}"
            )
            
        except requests.exceptions.Timeout:
            logger.warning(f"Telegram send timeout (attempt {attempt}/{retries})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Telegram connection error (attempt {attempt}/{retries})")
        except Exception as e:
            logger.error(f"Telegram send error (attempt {attempt}/{retries}): {e}")
        
        # Exponential backoff
        if attempt < retries:
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            time.sleep(delay)
    
    return False


def _send_message_with_keyboard(token, chat_id, text, reply_markup):
    """Send a message to Telegram with Inline Keyboard reply_markup."""
    if not token or not chat_id:
        return False
    if len(text) > TELEGRAM_MAX_MSG_LEN:
        text = text[:TELEGRAM_MAX_MSG_LEN - 20] + "\n\n... (truncated)"
    url = f"{TELEGRAM_API_URL}{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup,
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Error sending message with keyboard to chat {chat_id}: {e}")
        return False


def send_report_document(report_or_filepath, chat_id=None, caption=None):
    """
    Send a report document file (.pdf, .html, .json) to Telegram chat(s).
    
    Args:
        report_or_filepath (str|dict): File path string or report metadata dict.
        chat_id (int|str, optional): Target chat ID. If None, sends to all registered chats.
        caption (str, optional): Message caption.
        
    Returns:
        bool: True if sent successfully to at least one chat.
    """
    token = _get_bot_token()
    if not token:
        logger.warning("Telegram send_report_document failed: No bot token configured")
        return False
        
    filepath = None
    filename = None
    
    if isinstance(report_or_filepath, str):
        filepath = report_or_filepath
        filename = os.path.basename(filepath)
    elif isinstance(report_or_filepath, dict):
        filepath = report_or_filepath.get("file_path") or report_or_filepath.get("filepath")
        filename = report_or_filepath.get("filename") or (os.path.basename(filepath) if filepath else "report.pdf")
        
    if filepath and not os.path.isabs(filepath):
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        filepath = os.path.abspath(os.path.join(backend_dir, filepath))
        
    if not filepath or not os.path.exists(filepath):
        logger.error(f"Telegram send_report_document file not found: {filepath}")
        return False

    chat_ids = [chat_id] if chat_id else _get_all_chat_ids()
    if not chat_ids:
        logger.warning("Telegram send_report_document failed: No target chat IDs")
        return False
        
    cap = caption or f"📄 <b>ShadowTrap Incident Report</b>\n<code>{_escape(filename)}</code>"
    url = f"{TELEGRAM_API_URL}{token}/sendDocument"
    success = False
    
    for cid in chat_ids:
        try:
            with open(filepath, "rb") as f:
                files = {"document": (filename, f)}
                data = {"chat_id": cid, "caption": cap, "parse_mode": "HTML"}
                resp = requests.post(url, data=data, files=files, timeout=20)
                if resp.status_code == 200:
                    logger.info(f"Report document sent to Telegram chat {cid}: {filename}")
                    success = True
                else:
                    logger.error(f"Failed to send report to Telegram chat {cid}: HTTP {resp.status_code} — {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Error sending report document to Telegram chat {cid}: {e}")
            
    return success


# ─── Public Notification Functions ─────────────────────────

def send_test_message():
    """
    Send a test/connection verification message asynchronously in background thread.
    Prevents blocking server startup if Telegram API is slow or timing out.
    """
    token = _get_bot_token()
    if not token:
        logger.warning("TELEGRAM_STARTED — no bot token configured")
        return False
    
    chat_ids = _get_all_chat_ids()
    if not chat_ids:
        logger.warning("TELEGRAM_STARTED — no chat IDs configured (set TELEGRAM_CHAT_ID in .env or send /start to the bot)")
        return False
    
    def _async_send():
        now_ist = datetime.now(timezone.utc).astimezone(ist_tz).strftime("%Y-%m-%d %I:%M:%S %p")
        message = (
            f"🛡️ <b>ShadowTrap AI — Online</b>\n\n"
            f"✅ Connection verified at {now_ist}\n"
            f"📡 Monitoring active — you will receive high-value security alerts.\n"
            f"⚙️ Alert threshold: threat score ≥ {Config.AI_ALERT_THRESHOLD}"
        )
        for chat_id in chat_ids:
            if _send_message(token, chat_id, message, retries=2):
                logger.info(f"TELEGRAM_SENT test message to chat {chat_id}")
            else:
                logger.error(f"TELEGRAM_FAILED test message to chat {chat_id}")
    
    threading.Thread(target=_async_send, daemon=True).start()
    return True


def send_security_alert(attack_data, ai_analysis=None):
    """
    Send a security alert with AI copilot analysis to Telegram asynchronously.
    Runs in background thread so HTTP requests are never blocked.
    """
    token = _get_bot_token()
    if not token:
        return
    
    session_id = attack_data.get("session_id", "unknown")
    
    # Deduplication check
    if _is_duplicate_alert(session_id):
        logger.debug(f"TELEGRAM_STARTED session={session_id} — duplicate, skipping")
        return
    
    chat_ids = _get_all_chat_ids()
    if not chat_ids:
        logger.debug("No Telegram chat IDs available")
        return
    
    def _async_alert():
        logger.info(f"TELEGRAM_STARTED session={session_id}")
        message = _build_alert_message(attack_data, ai_analysis)
        for chat_id in chat_ids:
            if not _check_rate_limit(chat_id):
                logger.warning(f"Telegram rate limit reached for chat {chat_id}")
                continue
            if _send_message(token, chat_id, message):
                logger.info(f"TELEGRAM_SENT session={session_id} chat={chat_id}")
            else:
                logger.error(f"TELEGRAM_FAILED session={session_id} chat={chat_id}")

    threading.Thread(target=_async_alert, daemon=True).start()


def send_critical_alert(attack_data, ai_analysis=None):
    """Send an urgent critical-severity alert asynchronously."""
    token = _get_bot_token()
    if not token:
        return
    
    chat_ids = _get_all_chat_ids()
    if not chat_ids:
        return
    
    session_id = attack_data.get("session_id", "unknown")
    
    def _async_critical():
        message = "🔴🔴🔴 <b>CRITICAL THREAT DETECTED</b> 🔴🔴🔴\n\n"
        message += _build_alert_message(attack_data, ai_analysis)
        for chat_id in chat_ids:
            _send_message(token, chat_id, message)
            logger.info(f"TELEGRAM_SENT critical alert session={session_id} chat={chat_id}")

    threading.Thread(target=_async_critical, daemon=True).start()


def _build_alert_message(attack_data, ai_analysis=None):
    """Build a formatted Telegram alert message with AI analysis."""
    # Extract fields (escape all attacker-controlled data)
    ip = _escape(attack_data.get("src_ip", "Unknown"))
    port = _escape(str(attack_data.get("dst_port", "?")))
    session_id = _escape(attack_data.get("session_id", "Unknown"))
    protocol = _escape(attack_data.get("protocol", "?"))
    username = _escape(attack_data.get("username", ""))
    
    # Timestamp
    dt = attack_data.get("created_at", datetime.now(timezone.utc))
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    time_str = dt.astimezone(ist_tz).strftime("%Y-%m-%d %I:%M:%S %p") if hasattr(dt, 'astimezone') else str(dt)
    
    # Commands summary (truncated, escaped)
    commands = attack_data.get("commands", [])
    cmd_preview = ""
    if commands:
        preview_cmds = [_escape(cmd[:60]) for cmd in commands[:3]]
        cmd_preview = "\n".join([f"  • <code>{c}</code>" for c in preview_cmds])
        if len(commands) > 3:
            cmd_preview += f"\n  ... +{len(commands) - 3} more"
    
    # Base attack info
    threat_score = attack_data.get("threat_score", 0)
    stage = _escape(attack_data.get("attack_stage", "Unknown"))
    
    # Build message parts
    parts = [
        f"🚨 <b>Security Alert — ShadowTrap AI</b> 🚨\n",
        f"🕒 <b>Time:</b> {time_str}",
        f"🌐 <b>Source IP:</b> <code>{ip}</code>",
        f"🎯 <b>Target:</b> {protocol}:{port}",
    ]
    
    if username:
        parts.append(f"👤 <b>Username:</b> <code>{username}</code>")
    
    parts.append(f"📊 <b>Threat Score:</b> {threat_score}/100")
    parts.append(f"📍 <b>Attack Stage:</b> {stage}")
    
    if cmd_preview:
        parts.append(f"\n📝 <b>Commands:</b>\n{cmd_preview}")
    
    # AI Analysis section
    if ai_analysis and ai_analysis.get("source") != "none":
        threat_level = _escape(ai_analysis.get("threat_level", "N/A"))
        attack_type = _escape(ai_analysis.get("attack_type", "N/A"))
        confidence = ai_analysis.get("confidence", 0)
        risk_score = ai_analysis.get("risk_score", 0)
        next_move = _escape(str(ai_analysis.get("likely_next_move", "N/A"))[:200])
        action = _escape(str(ai_analysis.get("recommended_defensive_action", "N/A"))[:200])
        source = ai_analysis.get("source", "deterministic")
        
        parts.append(f"\n🤖 <b>AI Analysis</b> {'(Qwen)' if source == 'qwen_llm' else '(Deterministic)'}:")
        parts.append(f"  ⚠️ <b>Threat Level:</b> {threat_level}")
        parts.append(f"  🏷️ <b>Attack Type:</b> {attack_type}")
        parts.append(f"  📈 <b>Risk Score:</b> {risk_score}/100")
        parts.append(f"  🎯 <b>Confidence:</b> {confidence:.0%}")
        parts.append(f"  🔮 <b>Predicted Next Move:</b> {next_move}")
        parts.append(f"  🛡️ <b>Recommended Action:</b> {action}")
        
        # Deterministic prediction comparison
        det_pred = ai_analysis.get("deterministic_prediction", {})
        if det_pred.get("predicted_stage"):
            parts.append(
                f"  📊 <b>Markov Prediction:</b> {_escape(det_pred['predicted_stage'])} "
                f"({det_pred.get('confidence', 0)}%)"
            )
    
    parts.append(f"\n🆔 <b>Session:</b> <code>{session_id}</code>")
    
    return "\n".join(parts)


# ─── Telegram Bot Polling (interactive /report, callback queries) ─────

def _handle_updates(app, token):
    """Long-poll for Telegram bot commands and inline button callbacks."""
    offset = None
    from app.utils.helpers import utc_now
    from app.models.attack import get_recent_attacks
    from app.services.report_service import generate_report
    
    while True:
        try:
            url = f"{TELEGRAM_API_URL}{token}/getUpdates"
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            
            response = requests.get(url, params=params, timeout=40)
            data = response.json()
            
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    
                    # Handle Callback Queries (from Telegram Inline Keyboard buttons)
                    callback_query = update.get("callback_query")
                    if callback_query:
                        query_id = callback_query.get("id")
                        cq_data = callback_query.get("data", "")
                        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
                        
                        if query_id:
                            try:
                                requests.post(f"{TELEGRAM_API_URL}{token}/answerCallbackQuery", json={
                                    "callback_query_id": query_id,
                                    "text": "Generating & downloading PDF report..."
                                }, timeout=5)
                            except Exception:
                                pass
                                
                        if cq_data.startswith("dl_report:") and chat_id:
                            session_id = cq_data.split("dl_report:", 1)[1]
                            with app.app_context():
                                _send_message(token, chat_id, f"⏳ Generating PDF report for attack session <code>{_escape(session_id)}</code>...")
                                try:
                                    rep_doc = generate_report(session_id, format_type="pdf", user_id="telegram_bot")
                                    send_report_document(rep_doc, chat_id=chat_id, caption=f"📄 <b>Incident Report — {session_id}</b>\nDownloaded directly via Telegram.")
                                except Exception as err:
                                    logger.error(f"Telegram report generation error: {err}")
                                    _send_message(token, chat_id, f"❌ Failed to generate report: {_escape(str(err))}")
                        continue
                    
                    # Handle Standard Messages & Commands
                    message = update.get("message", {})
                    text = message.get("text", "")
                    chat_id = message.get("chat", {}).get("id")
                    
                    if not chat_id:
                        continue
                    
                    with app.app_context():
                        db = get_db()
                        # Register chat ID if not exists
                        db.telegram_chats.update_one(
                            {"chat_id": chat_id},
                            {"$setOnInsert": {"chat_id": chat_id, "registered_at": utc_now()}},
                            upsert=True
                        )
                        
                        cmd = text.strip()
                        cmd_lower = cmd.lower()
                        
                        if cmd_lower.startswith("/start"):
                            _send_message(
                                token, chat_id,
                                "🛡️ <b>Welcome to ShadowTrap AI!</b>\n\n"
                                "You are now registered for security alerts.\n"
                                f"Alert threshold: threat score ≥ {Config.AI_ALERT_THRESHOLD}\n\n"
                                "Commands:\n"
                                "📊 /report or /reports — Browse attacks & download PDF reports\n"
                                "📈 /history — Recent attacks summary\n"
                                "⚙️ /status — System status"
                            )
                            logger.info(f"Telegram chat {chat_id} registered via /start")
                            
                        elif cmd_lower.startswith("/report") or cmd_lower.startswith("/reports"):
                            attacks = get_recent_attacks(limit=6)
                            if not attacks:
                                _send_message(token, chat_id, "ℹ️ No attack sessions found to generate reports.")
                            else:
                                inline_keyboard = []
                                text_msg = "📁 <b>ShadowTrap Incident Reports</b>\n\nSelect an attack session below to download its PDF report instantly:"
                                for att in attacks:
                                    sid = att.get("session_id", "Unknown")
                                    ip = att.get("src_ip", "Unknown")
                                    score = att.get("threat_score", 0)
                                    stage = att.get("attack_stage", "Unknown")
                                    
                                    btn_text = f"📄 {sid} (IP: {ip} | Score: {score})"
                                    inline_keyboard.append([{"text": btn_text, "callback_data": f"dl_report:{sid}"}])
                                
                                reply_markup = {"inline_keyboard": inline_keyboard}
                                _send_message_with_keyboard(token, chat_id, text_msg, reply_markup)

                        elif cmd_lower.startswith("/dl_") or cmd_lower.startswith("/getreport_"):
                            # Direct command download e.g. /dl_SCAN-HTTP-127001
                            parts = cmd.split("_", 1)
                            if len(parts) > 1 and parts[1]:
                                session_id = parts[1].strip()
                                _send_message(token, chat_id, f"⏳ Generating PDF report for attack session <code>{_escape(session_id)}</code>...")
                                try:
                                    rep_doc = generate_report(session_id, format_type="pdf", user_id="telegram_bot")
                                    send_report_document(rep_doc, chat_id=chat_id, caption=f"📄 <b>Incident Report — {session_id}</b>\nDownloaded directly via Telegram.")
                                except Exception as err:
                                    _send_message(token, chat_id, f"❌ Failed to generate report: {_escape(str(err))}")
                                    
                        elif cmd_lower.startswith("/history"):
                            attacks = get_recent_attacks(limit=5)
                            if not attacks:
                                _send_message(token, chat_id, "No recent attacks found.")
                            else:
                                reply = "📊 <b>Recent Attacks:</b>\n\n"
                                for att in attacks:
                                    att_ip = _escape(att.get("src_ip", "?"))
                                    att_dt = att.get("created_at")
                                    if isinstance(att_dt, str):
                                        try:
                                            att_dt = datetime.fromisoformat(att_dt.replace("Z", "+00:00"))
                                        except Exception:
                                            att_dt = None
                                    
                                    if isinstance(att_dt, datetime):
                                        if att_dt.tzinfo is None:
                                            att_dt = att_dt.replace(tzinfo=timezone.utc)
                                        att_time = att_dt.astimezone(ist_tz).strftime("%I:%M:%S %p")
                                    else:
                                        att_time = "?"
                                    
                                    att_score = att.get("threat_score", 0)
                                    reply += f"🕒 {att_time} | IP: <code>{att_ip}</code> | Score: {att_score}\n"
                                reply += "\n💡 Type /report to select and download PDF reports."
                                _send_message(token, chat_id, reply)
                        
                        elif cmd_lower.startswith("/status"):
                            from app.services.llm_service import check_llm_health
                            health = check_llm_health()
                            status_icon = "✅" if health["available"] else "❌"
                            _send_message(
                                token, chat_id,
                                f"🛡️ <b>ShadowTrap AI Status</b>\n\n"
                                f"{status_icon} <b>Qwen AI:</b> {'Online' if health['available'] else 'Offline'}\n"
                                f"📡 <b>Model:</b> {_escape(health.get('model', '?'))}\n"
                                f"🔗 <b>Endpoint:</b> {_escape(health.get('endpoint', '?'))}\n"
                                f"⚙️ <b>Alert Threshold:</b> {Config.AI_ALERT_THRESHOLD}"
                            )
                        
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            time.sleep(2)
        except requests.exceptions.RequestException:
            time.sleep(2)
        except Exception as e:
            if "Connection aborted" in str(e) or "ConnectionResetError" in str(e):
                time.sleep(2)
            else:
                logger.error(f"Telegram polling error: {e}")
                time.sleep(5)



def start_telegram_bot(app):
    """Start the Telegram bot polling thread and send a test message."""
    token = _get_bot_token()
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not found — Telegram bot will not start.")
        return
    
    logger.info("TELEGRAM_STARTED — initializing bot...")
    
    # Send test message (uses app context from caller)
    send_test_message()
    
    # Start polling thread
    thread = threading.Thread(target=_handle_updates, args=(app, token), daemon=True)
    thread.start()
    logger.info("TELEGRAM_STARTED — polling thread running")


# ─── Legacy Compatibility ─────────────────────────────────

def send_telegram_notification(attack_data):
    """
    Legacy notification function called from attack.py create_attack().
    Now applies threshold filtering and delegates to send_security_alert().
    """
    threat_score = attack_data.get("threat_score", 0)
    
    if threat_score < Config.AI_ALERT_THRESHOLD:
        return  # Skip low-value events
    
    # Send with basic attack info (no AI analysis yet — that comes later from copilot)
    send_security_alert(attack_data, ai_analysis=None)
