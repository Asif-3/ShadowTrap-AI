"""
ShadowTrap AI - Intent Detector
==================================
Identifies attacker objectives from command patterns.

Intents:
    - Credential Theft
    - Data Theft
    - Persistence
    - Reconnaissance
    - Malware Deployment
    - Privilege Escalation
"""

from app.utils.logger import get_logger

logger = get_logger("ai.intent_detector")

INTENT_PATTERNS = {
    "Credential Theft": {
        "indicators": [
            "cat /etc/shadow", "cat /etc/passwd", "/etc/shadow",
            "passwd", "shadow", "credential", "password", "hash",
            "id_rsa", "authorized_keys", ".ssh/", "john", "hashcat",
            "mimikatz", ".mysql_history", ".bash_history",
            "wp-config", ".env", "config.php", "credentials",
            "secrets", "aws/credentials", "vault",
        ],
        "weight": 1.5,
    },
    "Data Theft": {
        "indicators": [
            "tar czf", "zip -r", "scp ", "sftp ", "rsync",
            "mysqldump", "pg_dump", "mongodump", "exfil",
            "upload", "curl -X POST", "POST -F",
            "/tmp/data", "dump", "backup", ".sql",
            "base64", "/dev/tcp", "customers", "financial",
        ],
        "weight": 1.4,
    },
    "Persistence": {
        "indicators": [
            "crontab", "useradd", "adduser", "systemctl enable",
            "rc.local", "authorized_keys >>", "backdoor",
            ">> /etc/passwd", "init.d", "systemd", ".bashrc",
            ".profile", "update-rc.d", "chkconfig",
        ],
        "weight": 1.3,
    },
    "Reconnaissance": {
        "indicators": [
            "whoami", "id", "uname", "hostname", "ifconfig",
            "ip addr", "netstat", "ps aux", "ls -la", "pwd",
            "find /", "cat /proc/", "env", "printenv", "df -h",
            "free -m", "uptime", "w", "who", "last", "arp -a",
            "nmap", "ip route", "ss -",
        ],
        "weight": 0.8,
    },
    "Malware Deployment": {
        "indicators": [
            "wget http", "curl -O http", "chmod +x", "chmod 777",
            ".sh", ".elf", "/tmp/", "bash ", "python -c",
            "perl -e", "loader", "miner", "botnet", "trojan",
            "rat", "implant", "beacon", "payload",
        ],
        "weight": 1.5,
    },
    "Privilege Escalation": {
        "indicators": [
            "sudo", "sudo su", "sudo -l", "su -", "su root",
            "-perm -4000", "SUID", "exploit", "gcc ", "make",
            "kernel", "priv", "escalat", "root", "uid=0",
            "pkexec", "/tmp/exploit",
        ],
        "weight": 1.4,
    },
}


def detect_intent(commands):
    """
    Detect attacker intent from command patterns.
    
    Args:
        commands: List of command strings
        
    Returns:
        dict: {
            "intent": str,
            "confidence": float (0-100),
            "all_intents": list of {intent, score, confidence},
            "evidence": list of matching commands
        }
    """
    if not commands:
        return {
            "intent": "Unknown",
            "confidence": 0,
            "all_intents": [],
            "evidence": [],
        }
    
    normalized = [cmd.lower().strip() for cmd in commands]
    
    intent_scores = {}
    intent_evidence = {}
    
    for intent_name, config in INTENT_PATTERNS.items():
        score = 0
        evidence = []
        
        for cmd in normalized:
            for indicator in config["indicators"]:
                if indicator.lower() in cmd:
                    score += 1.0 * config["weight"]
                    evidence.append(cmd)
                    break
        
        if score > 0:
            intent_scores[intent_name] = score
            intent_evidence[intent_name] = evidence
    
    if not intent_scores:
        return {
            "intent": "Reconnaissance",
            "confidence": 20.0,
            "all_intents": [{"intent": "Reconnaissance", "score": 0, "confidence": 20.0}],
            "evidence": [],
        }
    
    total = sum(intent_scores.values())
    all_intents = []
    
    for name, score in sorted(intent_scores.items(), key=lambda x: x[1], reverse=True):
        confidence = min(95, (score / max(total, 1)) * 100)
        all_intents.append({
            "intent": name,
            "score": round(score, 2),
            "confidence": round(confidence, 1),
        })
    
    primary = all_intents[0]
    
    return {
        "intent": primary["intent"],
        "confidence": primary["confidence"],
        "all_intents": all_intents,
        "evidence": intent_evidence.get(primary["intent"], []),
    }
