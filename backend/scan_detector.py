"""
ShadowTrap AI — Network Scan Detector
=======================================
Lightweight TCP listener that detects port scans (nmap, masscan, etc.)
and records them as real attacks in MongoDB + broadcasts via Socket.IO.

Listens on common honeypot ports and captures:
  - Source IP of the scanner
  - Scanned ports
  - Scan timing patterns
  - Service banner grabs

Usage:
    python scan_detector.py
"""

import os
import sys
import time
import socket
import threading
import json
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


# ── Ports to listen on (common nmap targets) ──
HONEYPOT_PORTS = [
    21,    # FTP
    23,    # Telnet
    25,    # SMTP
    80,    # HTTP
    110,   # POP3
    143,   # IMAP
    443,   # HTTPS
    445,   # SMB
    993,   # IMAPS
    995,   # POP3S
    1433,  # MSSQL
    3306,  # MySQL
    3389,  # RDP
    5432,  # PostgreSQL
    5900,  # VNC
    6379,  # Redis
    8443,  # HTTPS-Alt
]

# Service banners (fake responses to make nmap think services are real)
SERVICE_BANNERS = {
    21:   b"220 FTP Server Ready\r\n",
    22:   b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5\r\n",
    23:   b"\xff\xfd\x18\xff\xfd\x20\xff\xfd\x23\xff\xfd\x27",
    25:   b"220 mail.shadowtrap.local ESMTP Postfix\r\n",
    80:   b"HTTP/1.1 200 OK\r\nServer: Apache/2.4.41 (Ubuntu)\r\n\r\n",
    110:  b"+OK POP3 server ready\r\n",
    143:  b"* OK IMAP4rev1 Server Ready\r\n",
    443:  b"HTTP/1.1 200 OK\r\nServer: nginx/1.18.0\r\n\r\n",
    3306: b"\x4a\x00\x00\x00\x0a\x38\x2e\x30\x2e\x32\x37\x00",
    6379: b"-ERR unknown command\r\n",
}

# Scan aggregation window (seconds)
AGGREGATION_WINDOW = 10

# Minimum ports to count as a scan (1 port = connection probe, 3+ = scan)
MIN_PORTS_FOR_SCAN = 1


class ScanDetector:
    """Listens on multiple ports and detects network scanning activity."""

    def __init__(self, app=None):
        self.scan_buffer = defaultdict(lambda: {
            "ports": set(),
            "first_seen": None,
            "last_seen": None,
            "banner_grabs": 0,
            "data_received": [],
        })
        self.lock = threading.Lock()
        self.sockets = []
        self.running = False
        self.app = app
        self.db = None

    def start(self):
        """Start all port listeners and the flush thread."""
        if self.app is None:
            from app import create_app
            self.app = create_app()

        with self.app.app_context():
            from app.extensions import get_db
            self.db = get_db()

        self.running = True

        bound_ports = []
        # Start listener threads for each port
        for port in HONEYPOT_PORTS:
            t = threading.Thread(target=self._listen_port, args=(port,), daemon=True)
            t.start()

        # Start flush thread (periodically saves aggregated scans to DB)
        flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        flush_thread.start()

        print(f"""
    ╔══════════════════════════════════════════════════╗
    ║  🕸️  ShadowTrap AI — Network Scan Detector       ║
    ║                                                  ║
    ║  Listening on {len(HONEYPOT_PORTS):2d} honeypot ports              ║
    ║  Aggregation window: {AGGREGATION_WINDOW}s                     ║
    ║  Ready to capture nmap/masscan/zmap scans        ║
    ╚══════════════════════════════════════════════════╝
        """)

        print(f"  Ports: {', '.join(str(p) for p in HONEYPOT_PORTS)}")
        print()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Scan Detector stopped.")
            self.running = False

    def _listen_port(self, port):
        """Listen on a single port for incoming connections."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(1.0)
            sock.bind(("0.0.0.0", port))
            sock.listen(5)
            self.sockets.append(sock)
            print(f"  ✓ Listening on port {port}")
        except OSError as e:
            print(f"  ✗ Cannot bind port {port}: {e}")
            return

        while self.running:
            try:
                conn, addr = sock.accept()
                # Handle each connection in its own thread
                t = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, addr, port),
                    daemon=True
                )
                t.start()
            except socket.timeout:
                continue
            except Exception:
                continue

    def _handle_connection(self, conn, addr, port):
        """Handle an individual connection from a scanner."""
        src_ip = addr[0]
        src_port = addr[1]
        now = datetime.now(timezone.utc)
        received_data = b""

        try:
            conn.settimeout(3)

            # Send fake banner to make nmap service detection work
            banner = SERVICE_BANNERS.get(port, b"")
            if banner:
                try:
                    conn.sendall(banner)
                except Exception:
                    pass

            # Try to read any data the scanner sends
            try:
                received_data = conn.recv(4096)
            except Exception:
                pass

        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

        # Record this connection event
        with self.lock:
            entry = self.scan_buffer[src_ip]
            entry["ports"].add(port)
            if entry["first_seen"] is None:
                entry["first_seen"] = now
            entry["last_seen"] = now
            if received_data:
                entry["banner_grabs"] += 1
                entry["data_received"].append({
                    "port": port,
                    "data": received_data[:200].hex(),
                    "timestamp": now.isoformat(),
                })

        print(
            f"  🔴 Connection: {src_ip}:{src_port} → port {port} "
            f"(total ports scanned: {len(self.scan_buffer[src_ip]['ports'])})"
        )

    def _flush_loop(self):
        """Periodically flush aggregated scan events to MongoDB."""
        while self.running:
            time.sleep(AGGREGATION_WINDOW)
            self._flush_scans()

    def _flush_scans(self):
        """Convert buffered scan data into attack records."""
        with self.lock:
            to_flush = {}
            now = datetime.now(timezone.utc)

            for ip, data in list(self.scan_buffer.items()):
                # Only flush if the scan has been idle for the aggregation window
                if data["last_seen"] and (now - data["last_seen"]).total_seconds() >= AGGREGATION_WINDOW / 2:
                    to_flush[ip] = data
                    del self.scan_buffer[ip]

        if not to_flush:
            return

        with self.app.app_context():
            from app.extensions import get_db
            from app.models.attack import create_attack
            from app.ai.stage_detector import detect_stage
            from app.ai.intent_detector import detect_intent
            from app.services.threat_score_service import calculate_threat_score
            from app.socketio_events import broadcast_new_attack, broadcast_dashboard_update

            db = get_db()

            for src_ip, scan_data in to_flush.items():
                ports = sorted(scan_data["ports"])
                port_count = len(ports)
                first_seen = scan_data["first_seen"]
                last_seen = scan_data["last_seen"]
                duration = (last_seen - first_seen).total_seconds() if first_seen and last_seen else 0

                # Build synthetic commands from scan activity
                commands = []
                commands.append(f"nmap scan detected from {src_ip}")
                commands.append(f"Scanned {port_count} port(s): {', '.join(str(p) for p in ports[:30])}")

                if scan_data["banner_grabs"] > 0:
                    commands.append(f"Service version detection: {scan_data['banner_grabs']} banner grab(s)")

                # Map scanned ports to service names
                port_services = {
                    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
                    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
                    993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 3306: "MySQL",
                    3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
                    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB"
                }
                detected_services = [f"{port_services.get(p, 'Unknown')}/{p}" for p in ports if p in port_services]
                if detected_services:
                    commands.append(f"Services found: {', '.join(detected_services)}")

                # Determine scan type
                if port_count >= 15:
                    scan_type = "Full Port Scan"
                elif port_count >= 5:
                    scan_type = "Targeted Service Scan"
                else:
                    scan_type = "Port Probe"
                commands.append(f"Scan classification: {scan_type}")

                # Generate session ID
                session_id = f"SCAN-{src_ip.replace('.', '')}-{int(first_seen.timestamp())}"

                # Run AI analysis
                stage_result = detect_stage(commands)
                intent_result = detect_intent(commands)

                # Calculate threat score
                base_score = min(25 + port_count * 3, 95)
                if scan_data["banner_grabs"] > 0:
                    base_score = min(base_score + 15, 98)

                # Build attack document
                attack_data = {
                    "session_id": session_id,
                    "src_ip": src_ip,
                    "src_port": 0,
                    "dst_port": ports[0] if ports else 0,
                    "protocol": "TCP",
                    "username": "",
                    "password": "",
                    "commands": commands,
                    "timestamps": [first_seen.isoformat(), last_seen.isoformat()],
                    "downloaded_files": [],
                    "executed_files": [],
                    "start_time": first_seen,
                    "end_time": last_seen,
                    "duration": duration,
                    "command_count": len(commands),
                    "status": "analyzed",
                    "threat_score": base_score,
                    "attack_stage": stage_result.get("stage", "Reconnaissance"),
                    "intent": intent_result.get("intent", "Reconnaissance"),
                    "persona": {
                        "skill_level": "Advanced" if port_count >= 10 else "Intermediate" if port_count >= 3 else "Novice",
                        "attack_style": scan_type,
                        "persistence_level": "High" if port_count >= 10 else "Medium",
                    },
                    "is_live": False,
                    "scan_metadata": {
                        "scan_type": scan_type,
                        "ports_scanned": ports,
                        "port_count": port_count,
                        "banner_grabs": scan_data["banner_grabs"],
                        "detected_services": detected_services,
                        "raw_data_samples": scan_data["data_received"][:5],
                    },
                }

                # Store in database
                create_attack(attack_data)

                # Store analysis results
                from app.utils.helpers import utc_now
                db.attack_stages.update_one(
                    {"session_id": session_id},
                    {"$set": {**stage_result, "session_id": session_id, "detected_at": utc_now()}},
                    upsert=True
                )
                db.intents.update_one(
                    {"session_id": session_id},
                    {"$set": {**intent_result, "session_id": session_id, "detected_at": utc_now()}},
                    upsert=True
                )
                db.threat_scores.update_one(
                    {"session_id": session_id},
                    {"$set": {"score": base_score, "session_id": session_id, "calculated_at": utc_now()}},
                    upsert=True
                )

                # Broadcast to admin dashboard via Socket.IO
                try:
                    broadcast_new_attack({
                        "session_id": session_id,
                        "src_ip": src_ip,
                        "protocol": "TCP",
                        "dst_port": ports[0] if ports else 0,
                        "threat_score": base_score,
                        "attack_stage": attack_data["attack_stage"],
                        "intent": attack_data["intent"],
                        "command_count": len(commands),
                        "status": "analyzed",
                        "created_at": first_seen.isoformat(),
                    })
                    broadcast_dashboard_update()
                except Exception as e:
                    print(f"  ⚠ Socket.IO broadcast error: {e}")

                print(
                    f"\n  ✅ ATTACK RECORDED: {session_id}"
                    f"\n     IP: {src_ip} | Ports: {port_count} | Score: {base_score}"
                    f"\n     Stage: {attack_data['attack_stage']} | Intent: {attack_data['intent']}"
                    f"\n"
                )


if __name__ == "__main__":
    detector = ScanDetector()
    detector.start()
