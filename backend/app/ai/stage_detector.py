"""
ShadowTrap AI - Attack Stage Detector
=======================================
Detects the current attack stage from attacker commands using
rule-based classification with confidence scoring.

Stages:
    1. Reconnaissance
    2. Discovery
    3. Credential Discovery
    4. Payload Download
    5. Privilege Escalation
    6. Persistence
    7. Defense Evasion
    8. Command And Control
    9. Data Collection
   10. Exfiltration
"""

from app.utils.logger import get_logger

logger = get_logger("ai.stage_detector")

# ── Stage Definitions & Command Patterns ─────────────────
STAGE_PATTERNS = {
    "Reconnaissance": {
        "commands": [
            "nmap", "masscan", "ping", "traceroute", "dig", "nslookup",
            "host", "whois", "finger", "showmount",
        ],
        "patterns": [
            "scan", "probe", "enum", "recon",
        ],
        "weight": 1.0,
    },
    "Discovery": {
        "commands": [
            "whoami", "id", "uname", "hostname", "ifconfig", "ip addr",
            "netstat", "ss", "ps", "top", "w", "who", "last", "uptime",
            "cat /proc", "cat /etc/os-release", "lsb_release", "df",
            "free", "mount", "lsblk", "fdisk", "cat /proc/cpuinfo",
            "cat /proc/version", "dpkg", "rpm", "env", "printenv",
            "ls", "pwd", "find", "locate", "arp", "route", "ip route",
        ],
        "patterns": [
            "ls -", "find /", "cat /etc/", "cat /proc/",
            "ip addr", "netstat -", "ss -", "ps aux",
            "dpkg -l", "rpm -qa",
        ],
        "weight": 0.8,
    },
    "Credential Discovery": {
        "commands": [
            "cat /etc/passwd", "cat /etc/shadow", "cat /etc/group",
            "cat /etc/sudoers", "cat /etc/ssh/sshd_config",
            "cat /root/.ssh/authorized_keys", "cat /root/.bash_history",
            "strings", "grep password", "grep -r password",
        ],
        "patterns": [
            "/etc/shadow", "/etc/passwd", "passwd", "shadow",
            "authorized_keys", "id_rsa", "id_dsa", ".ssh/",
            "credentials", "password", "secret", ".env",
            "wp-config", "config.php", ".mysql_history",
            ".bash_history", ".aws/credentials",
        ],
        "weight": 1.2,
    },
    "Payload Download": {
        "commands": [
            "wget", "curl -O", "curl -o", "fetch", "tftp",
            "ftp", "scp", "rsync",
        ],
        "patterns": [
            "wget http", "curl -O http", "curl -o ",
            "curl http", "download", ".sh", ".elf", ".py",
            "base64 -d", "python -c", "perl -e",
        ],
        "weight": 1.5,
    },
    "Privilege Escalation": {
        "commands": [
            "sudo", "sudo su", "sudo -l", "su", "su -",
            "pkexec", "doas",
        ],
        "patterns": [
            "sudo ", "su -", "su root", "chmod u+s",
            "-perm -4000", "SUID", "kernel_exploit",
            "exploit", "priv", "escalat", "/tmp/exploit",
            "gcc ", "make", "compile",
        ],
        "weight": 1.4,
    },
    "Persistence": {
        "commands": [
            "crontab", "crontab -e", "systemctl enable",
            "chkconfig", "update-rc.d", "useradd", "adduser",
            "usermod", "passwd",
        ],
        "patterns": [
            "crontab", "cron", "systemctl enable", "rc.local",
            "authorized_keys", "/etc/passwd >>", "useradd",
            "adduser", "backdoor", "persistence", ">> /etc",
            ".bashrc", ".profile", "init.d", "systemd",
        ],
        "weight": 1.3,
    },
    "Defense Evasion": {
        "commands": [
            "history -c", "unset HISTFILE", "rm -rf /var/log",
            "iptables -F", "systemctl stop firewalld",
            "setenforce 0", "ufw disable",
        ],
        "patterns": [
            "history -c", "HISTFILE", "/var/log", "rm -rf",
            "rm -f", "iptables -F", "firewalld", "ufw disable",
            "selinux", "apparmor", "shred", "wipe",
            "export HISTFILE=/dev/null", "touch -t",
        ],
        "weight": 1.3,
    },
    "Command And Control": {
        "commands": [
            "nc", "netcat", "ncat", "socat",
        ],
        "patterns": [
            "nc -", "netcat", "reverse", "shell", "bind",
            "callback", "beacon", "c2", "c&c",
            "stratum", "pool", "miner",
            "/dev/tcp/", "bash -i",
        ],
        "weight": 1.5,
    },
    "Data Collection": {
        "commands": [
            "tar", "zip", "gzip", "bzip2", "7z",
            "mysqldump", "pg_dump", "mongodump",
        ],
        "patterns": [
            "tar czf", "tar -czf", "zip -r", "mysqldump",
            "pg_dump", "mongodump", "cp /", "find / -name",
            "collect", "dump", "backup", "archive",
        ],
        "weight": 1.2,
    },
    "Exfiltration": {
        "commands": [
            "scp", "sftp", "rsync", "ftp", "tftp",
        ],
        "patterns": [
            "scp ", "sftp ", "curl -X POST", "curl --upload",
            "exfil", "upload", "POST -F", "nc ",
            "base64 | curl", "/upload", ">> /dev/tcp",
        ],
        "weight": 1.5,
    },
}


def detect_stage(commands):
    """
    Detect the attack stage from a list of attacker commands.
    
    Uses weighted pattern matching across all stage definitions.
    Returns the highest-scoring stage with confidence.
    
    Args:
        commands: List of command strings from the attacker session
        
    Returns:
        dict: {
            "stage": str,
            "confidence": float (0-100),
            "all_stages": list of {stage, score, confidence},
            "evidence": list of matching commands per stage
        }
    """
    if not commands:
        return {
            "stage": "Unknown",
            "confidence": 0,
            "all_stages": [],
            "evidence": [],
        }
    
    # Normalize commands to lowercase for matching
    normalized = [cmd.lower().strip() for cmd in commands]
    
    stage_scores = {}
    stage_evidence = {}
    
    for stage_name, patterns in STAGE_PATTERNS.items():
        score = 0
        evidence = []
        
        for cmd in normalized:
            matched = False
            
            # Check exact command matches
            for known_cmd in patterns["commands"]:
                if cmd == known_cmd.lower() or cmd.startswith(known_cmd.lower()):
                    score += 1.0 * patterns["weight"]
                    matched = True
                    break
            
            # Check pattern matches (substring)
            if not matched:
                for pattern in patterns["patterns"]:
                    if pattern.lower() in cmd:
                        score += 0.7 * patterns["weight"]
                        matched = True
                        break
            
            if matched:
                evidence.append(cmd)
        
        if score > 0:
            stage_scores[stage_name] = score
            stage_evidence[stage_name] = evidence
    
    if not stage_scores:
        return {
            "stage": "Discovery",  # Default stage
            "confidence": 25.0,
            "all_stages": [{"stage": "Discovery", "score": 0, "confidence": 25.0}],
            "evidence": [],
        }
    
    # Calculate confidence scores
    total_score = sum(stage_scores.values())
    all_stages = []
    
    for stage_name, score in sorted(stage_scores.items(), key=lambda x: x[1], reverse=True):
        confidence = min(95, (score / max(total_score, 1)) * 100)
        all_stages.append({
            "stage": stage_name,
            "score": round(score, 2),
            "confidence": round(confidence, 1),
        })
    
    # Primary stage is the highest scoring
    primary = all_stages[0]
    
    return {
        "stage": primary["stage"],
        "confidence": primary["confidence"],
        "all_stages": all_stages,
        "evidence": stage_evidence.get(primary["stage"], []),
    }


def detect_all_stages_timeline(commands, timestamps=None):
    """
    Detect attack stages over time, showing progression.
    
    Args:
        commands: List of command strings
        timestamps: Optional list of timestamp strings
        
    Returns:
        List of stage transitions with timestamps
    """
    timeline = []
    
    for i, cmd in enumerate(commands):
        result = detect_stage([cmd])
        
        entry = {
            "command": cmd,
            "stage": result["stage"],
            "confidence": result["confidence"],
            "index": i,
        }
        
        if timestamps and i < len(timestamps):
            entry["timestamp"] = timestamps[i]
        
        # Only add if stage changed or first entry
        if not timeline or timeline[-1]["stage"] != entry["stage"]:
            timeline.append(entry)
    
    return timeline
