"""
ShadowTrap AI X — Cyber Kill Chain Mapping Service
=====================================================
Maps attacker command execution sequences to the Lockheed Martin Cyber Kill Chain:
    1. Reconnaissance
    2. Weaponization
    3. Delivery
    4. Exploitation
    5. Installation
    6. Command & Control (C2)
    7. Actions on Objectives
"""

KILL_CHAIN_STAGES = [
    "Reconnaissance",
    "Weaponization",
    "Delivery",
    "Exploitation",
    "Installation",
    "Command & Control",
    "Actions on Objectives"
]

def map_to_kill_chain(commands, stage_name=""):
    """
    Map session commands to standard Cyber Kill Chain phases.

    Args:
        commands: List of command strings
        stage_name: Current primary detected stage

    Returns:
        dict: {
            "current_phase": str,
            "phase_progression": list of {phase, achieved, evidence},
            "completion_percentage": float
        }
    """
    cmd_text = " ".join(commands).lower()

    achieved = {phase: False for phase in KILL_CHAIN_STAGES}
    evidence = {phase: [] for phase in KILL_CHAIN_STAGES}

    # Reconnaissance
    if any(k in cmd_text for k in ["nmap", "ping", "whoami", "id", "uname", "ip addr", "netstat", "ps"]):
        achieved["Reconnaissance"] = True
        evidence["Reconnaissance"] = [c for c in commands if any(k in c.lower() for k in ["nmap", "ping", "whoami", "id", "uname", "ip", "netstat"])][:3]

    # Weaponization
    if any(k in cmd_text for k in ["base64", "gcc", "make", "python -c", "perl -e"]):
        achieved["Weaponization"] = True
        evidence["Weaponization"] = [c for c in commands if any(k in c.lower() for k in ["base64", "gcc", "make", "python", "perl"])][:3]

    # Delivery
    if any(k in cmd_text for k in ["wget", "curl", "fetch", "tftp", "scp"]):
        achieved["Delivery"] = True
        evidence["Delivery"] = [c for c in commands if any(k in c.lower() for k in ["wget", "curl", "fetch", "tftp", "scp"])][:3]

    # Exploitation
    if any(k in cmd_text for k in ["sudo", "su root", "chmod u+s", "pkexec"]):
        achieved["Exploitation"] = True
        evidence["Exploitation"] = [c for c in commands if any(k in c.lower() for k in ["sudo", "su", "chmod", "pkexec"])][:3]

    # Installation
    if any(k in cmd_text for k in ["crontab", "systemctl enable", "rc.local", "useradd"]):
        achieved["Installation"] = True
        evidence["Installation"] = [c for c in commands if any(k in c.lower() for k in ["crontab", "systemctl", "rc.local", "useradd"])][:3]

    # Command & Control
    if any(k in cmd_text for k in ["nc", "netcat", "socat", "/dev/tcp", "bash -i"]):
        achieved["Command & Control"] = True
        evidence["Command & Control"] = [c for c in commands if any(k in c.lower() for k in ["nc", "netcat", "socat", "/dev/tcp", "bash"])][:3]

    # Actions on Objectives
    if any(k in cmd_text for k in ["tar", "zip", "mysqldump", "/etc/shadow", "rm -rf /var/log"]):
        achieved["Actions on Objectives"] = True
        evidence["Actions on Objectives"] = [c for c in commands if any(k in c.lower() for k in ["tar", "zip", "mysqldump", "shadow", "rm"])][:3]

    progression = []
    achieved_count = 0
    highest_phase = "Reconnaissance"

    for phase in KILL_CHAIN_STAGES:
        is_achieved = achieved[phase]
        if is_achieved:
            achieved_count += 1
            highest_phase = phase
        progression.append({
            "phase": phase,
            "achieved": is_achieved,
            "evidence": evidence[phase]
        })

    completion_pct = round((achieved_count / len(KILL_CHAIN_STAGES)) * 100, 1)

    return {
        "current_phase": highest_phase,
        "phase_progression": progression,
        "completion_percentage": completion_pct
    }
