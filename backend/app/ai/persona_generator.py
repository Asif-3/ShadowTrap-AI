"""
ShadowTrap AI - Attacker Persona Generator
=============================================
Generates attacker profiles based on behavioral analysis
of command patterns, timing, and sophistication level.

Persona Attributes:
    - Skill Level: Beginner, Intermediate, Advanced, Expert
    - Attack Style: Manual, Automated, Mixed
    - Likely Goal: string description
    - Risk: Low, Medium, High, Critical
    - Threat Level: 1-10
    - Confidence: 0-100%
"""

import re
from app.utils.logger import get_logger

logger = get_logger("ai.persona")

# ── Sophistication Indicators ────────────────────────────
EXPERT_INDICATORS = [
    "gcc", "make", "python -c", "perl -e", "ruby -e",
    "awk", "sed", "base64", "openssl", "/dev/tcp",
    "socat", "nmap -s", "metasploit", "msfvenom",
    "kernel_exploit", "CVE-", "0day", "buffer overflow",
    "shellcode", "reverse shell", "bind shell",
]

ADVANCED_INDICATORS = [
    "find / -perm", "SUID", "sudo -l", "crontab",
    "systemctl", "iptables", "useradd", "netcat",
    "nc -", "curl -X POST", "scp ", "sftp ",
    "mysqldump", "pg_dump", "tar czf", "history -c",
    "unset HISTFILE", "rm -rf /var/log",
]

INTERMEDIATE_INDICATORS = [
    "wget http", "curl -O", "chmod +x", "cat /etc/shadow",
    "cat /etc/passwd", "sudo su", "su -", "ps aux",
    "netstat -tlnp", "ifconfig", "ip addr",
]

BEGINNER_INDICATORS = [
    "whoami", "id", "uname", "hostname", "pwd", "ls",
    "ls -la", "cat", "cd", "echo", "uptime", "w", "who",
    "last", "free", "df",
]

# ── Automation Patterns ──────────────────────────────────
AUTOMATED_PATTERNS = [
    r"&&\s*\w+",       # Chained commands
    r"\|\s*\w+",       # Piped commands
    r";\s*\w+",        # Semicolon chains
    r"for\s+\w+\s+in", # For loops
    r"while\s+",       # While loops
    r"2>/dev/null",    # Output redirection (automated scripts)
    r"\$\(",           # Command substitution
]


def generate_persona(commands, duration=0, timestamps=None):
    """
    Generate an attacker persona from behavioral analysis.
    
    Args:
        commands: List of command strings
        duration: Session duration in seconds
        timestamps: Optional list of timestamp strings
        
    Returns:
        dict: {
            "skill_level": str,
            "attack_style": str,
            "likely_goal": str,
            "risk": str,
            "threat_level": int (1-10),
            "confidence": float (0-100),
            "behavioral_traits": list of str,
            "sophistication_score": float (0-100)
        }
    """
    if not commands:
        return _default_persona()
    
    normalized = [cmd.lower().strip() for cmd in commands]
    
    # ── Skill Level Assessment ────────────────────────────
    skill_score = _assess_skill_level(normalized)
    skill_level = _score_to_skill(skill_score)
    
    # ── Attack Style Detection ────────────────────────────
    attack_style = _detect_attack_style(normalized, duration)
    
    # ── Goal Inference ────────────────────────────────────
    likely_goal = _infer_goal(normalized)
    
    # ── Risk Assessment ───────────────────────────────────
    risk_level, threat_level = _assess_risk(
        normalized, skill_score, duration
    )
    
    # ── Behavioral Traits ─────────────────────────────────
    traits = _extract_traits(normalized, skill_level, attack_style)
    
    # ── Confidence ────────────────────────────────────────
    confidence = min(95, 30 + (len(commands) * 5) + (skill_score * 0.3))
    
    return {
        "skill_level": skill_level,
        "attack_style": attack_style,
        "likely_goal": likely_goal,
        "risk": risk_level,
        "threat_level": threat_level,
        "confidence": round(confidence, 1),
        "behavioral_traits": traits,
        "sophistication_score": round(skill_score, 1),
    }


def _assess_skill_level(commands):
    """Calculate sophistication score (0-100)."""
    score = 0
    unique_commands = set(commands)
    
    for cmd in unique_commands:
        for indicator in EXPERT_INDICATORS:
            if indicator.lower() in cmd:
                score += 15
                break
        for indicator in ADVANCED_INDICATORS:
            if indicator.lower() in cmd:
                score += 8
                break
        for indicator in INTERMEDIATE_INDICATORS:
            if indicator.lower() in cmd:
                score += 4
                break
        for indicator in BEGINNER_INDICATORS:
            if indicator.lower() in cmd:
                score += 1
                break
    
    # Bonus for variety
    if len(unique_commands) > 10:
        score += 10
    if len(unique_commands) > 20:
        score += 15
    
    # Bonus for complex command chains
    for cmd in commands:
        if "&&" in cmd or "|" in cmd:
            score += 3
        if "2>/dev/null" in cmd:
            score += 5
    
    return min(100, score)


def _score_to_skill(score):
    """Convert sophistication score to skill level label."""
    if score >= 70:
        return "Expert"
    elif score >= 45:
        return "Advanced"
    elif score >= 20:
        return "Intermediate"
    else:
        return "Beginner"


def _detect_attack_style(commands, duration):
    """Determine if attack is manual, automated, or mixed."""
    automated_count = 0
    total = len(commands)
    
    for cmd in commands:
        for pattern in AUTOMATED_PATTERNS:
            if re.search(pattern, cmd):
                automated_count += 1
                break
    
    if total == 0:
        return "Unknown"
    
    automation_ratio = automated_count / total
    
    # Very fast session with many commands = likely automated
    if duration > 0 and total > 0:
        commands_per_second = total / max(duration, 1)
        if commands_per_second > 0.5:
            return "Automated"
    
    if automation_ratio > 0.5:
        return "Automated"
    elif automation_ratio > 0.15:
        return "Mixed"
    else:
        return "Manual"


def _infer_goal(commands):
    """Infer the most likely attacker goal."""
    cmd_text = " ".join(commands)
    
    goal_indicators = {
        "Cryptomining / Resource Hijacking": [
            "miner", "stratum", "pool", "xmrig", "cryptonight"
        ],
        "Data Exfiltration": [
            "scp", "sftp", "upload", "exfil", "curl -X POST",
            "POST -F", "mysqldump", "tar czf"
        ],
        "Botnet Recruitment": [
            "botnet", "loader", "bot", "ddos", "flood",
            "amplification"
        ],
        "Backdoor Installation": [
            "backdoor", "useradd", "authorized_keys >>",
            "crontab", "persistence", ">> /etc/passwd"
        ],
        "Credential Harvesting": [
            "/etc/shadow", "/etc/passwd", "credentials",
            "password", "hash", "id_rsa", "wp-config"
        ],
        "System Reconnaissance": [
            "whoami", "uname", "ifconfig", "nmap", "netstat"
        ],
        "Ransomware Deployment": [
            "encrypt", "ransom", "bitcoin", "wallet", "gpg -e"
        ],
    }
    
    goal_scores = {}
    for goal, indicators in goal_indicators.items():
        score = sum(1 for ind in indicators if ind in cmd_text)
        if score > 0:
            goal_scores[goal] = score
    
    if not goal_scores:
        return "General System Compromise"
    
    return max(goal_scores, key=goal_scores.get)


def _assess_risk(commands, skill_score, duration):
    """Assess overall risk level and threat level (1-10)."""
    risk_score = 0
    
    # High-risk commands
    high_risk = ["rm -rf", "wget", "curl -O", "chmod", "useradd",
                 "crontab", "iptables", "sudo", "/etc/shadow"]
    for cmd in commands:
        for hr in high_risk:
            if hr in cmd:
                risk_score += 2
                break
    
    # Factor in skill level
    risk_score += skill_score * 0.3
    
    # Factor in command count
    risk_score += min(20, len(commands) * 1.5)
    
    # Calculate threat level (1-10)
    threat_level = min(10, max(1, int(risk_score / 8)))
    
    # Risk label
    if risk_score >= 50:
        risk = "Critical"
    elif risk_score >= 30:
        risk = "High"
    elif risk_score >= 15:
        risk = "Medium"
    else:
        risk = "Low"
    
    return risk, threat_level


def _extract_traits(commands, skill_level, attack_style):
    """Extract behavioral traits from command patterns."""
    traits = []
    cmd_text = " ".join(commands)
    
    if "history -c" in cmd_text or "HISTFILE" in cmd_text:
        traits.append("Evidence-aware: Attempts to clear command history")
    
    if "rm -rf /var/log" in cmd_text or "rm -rf /var" in cmd_text:
        traits.append("Anti-forensic: Deletes system logs")
    
    if "/etc/shadow" in cmd_text or "/etc/passwd" in cmd_text:
        traits.append("Credential-focused: Targets authentication databases")
    
    if "wget" in cmd_text or "curl -O" in cmd_text:
        traits.append("Tool-bringer: Downloads external tools/payloads")
    
    if "crontab" in cmd_text or "systemctl" in cmd_text:
        traits.append("Persistence-seeker: Sets up recurring access")
    
    if "nmap" in cmd_text or "netstat" in cmd_text:
        traits.append("Network-mapper: Performs network reconnaissance")
    
    if "sudo" in cmd_text or "su " in cmd_text:
        traits.append("Privilege-hunter: Attempts privilege escalation")
    
    if "iptables" in cmd_text or "firewall" in cmd_text:
        traits.append("Defense-disabler: Attempts to weaken security controls")
    
    if "scp" in cmd_text or "sftp" in cmd_text or "upload" in cmd_text:
        traits.append("Data-exfiltrator: Transfers data to external servers")
    
    if not traits:
        traits.append(f"{skill_level} {attack_style.lower()} attacker")
    
    return traits


def _default_persona():
    """Return default persona for empty command sets."""
    return {
        "skill_level": "Unknown",
        "attack_style": "Unknown",
        "likely_goal": "Unknown",
        "risk": "Low",
        "threat_level": 1,
        "confidence": 0,
        "behavioral_traits": [],
        "sophistication_score": 0,
    }
