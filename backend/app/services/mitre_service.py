"""
ShadowTrap AI X — MITRE ATT&CK Service
==========================================
Maps commands to MITRE ATT&CK techniques, tactics, and provides matrix visualization structures.
"""

import json
import os
from app.utils.logger import get_logger

logger = get_logger("services.mitre")

_mitre_mapping = None

FULL_MITRE_TACTICS = [
    {"id": "TA0043", "name": "Reconnaissance"},
    {"id": "TA0042", "name": "Resource Development"},
    {"id": "TA0001", "name": "Initial Access"},
    {"id": "TA0002", "name": "Execution"},
    {"id": "TA0003", "name": "Persistence"},
    {"id": "TA0004", "name": "Privilege Escalation"},
    {"id": "TA0005", "name": "Defense Evasion"},
    {"id": "TA0006", "name": "Credential Access"},
    {"id": "TA0007", "name": "Discovery"},
    {"id": "TA0008", "name": "Lateral Movement"},
    {"id": "TA0009", "name": "Collection"},
    {"id": "TA0011", "name": "Command and Control"},
    {"id": "TA0010", "name": "Exfiltration"},
    {"id": "TA0040", "name": "Impact"},
]


def _load_mitre_mapping():
    global _mitre_mapping
    if _mitre_mapping is not None:
        return _mitre_mapping

    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "mitre_mapping.json"
    )

    try:
        with open(path, "r", encoding="utf-8") as f:
            _mitre_mapping = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load MITRE mapping: {e}")
        _mitre_mapping = {}

    return _mitre_mapping


def map_commands(commands):
    """
    Map list of commands to MITRE ATT&CK techniques.

    Args:
        commands: List of command strings

    Returns:
        list of {technique_id, technique_name, tactic, description, matched_command}
    """
    mapping = _load_mitre_mapping()
    results = []
    seen = set()

    for cmd in commands:
        cmd_lower = cmd.lower().strip()
        cmd_base = cmd_lower.split()[0] if cmd_lower else ""

        matched = False
        for known_cmd, tech in mapping.items():
            if known_cmd.lower() in cmd_lower or cmd_base == known_cmd.lower():
                key = (tech.get("technique_id"), tech.get("tactic"))
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "technique_id": tech.get("technique_id", "N/A"),
                        "technique_name": tech.get("technique_name", "N/A"),
                        "tactic": tech.get("tactic", "N/A"),
                        "description": tech.get("description", ""),
                        "matched_command": cmd,
                    })
                matched = True

        if not matched and cmd_base:
            tech_info = _infer_mitre(cmd_base, cmd_lower)
            if tech_info:
                key = (tech_info["technique_id"], tech_info["tactic"])
                if key not in seen:
                    seen.add(key)
                    tech_info["matched_command"] = cmd
                    results.append(tech_info)

    return results


def _infer_mitre(cmd_base, cmd_full):
    if cmd_base in ("whoami", "id", "uname", "hostname"):
        return {"technique_id": "T1033", "technique_name": "System Owner/User Discovery", "tactic": "Discovery", "description": "Identify current user account and system details."}
    elif cmd_base in ("ifconfig", "ip", "netstat", "ss", "arp", "route"):
        return {"technique_id": "T1049", "technique_name": "System Network Connections Discovery", "tactic": "Discovery", "description": "Identify active network connections and interfaces."}
    elif cmd_base in ("wget", "curl", "fetch", "tftp"):
        return {"technique_id": "T1105", "technique_name": "Ingress Tool Transfer", "tactic": "Command and Control", "description": "Download external malicious files/tools."}
    elif cmd_base in ("sudo", "su", "pkexec"):
        return {"technique_id": "T1548", "technique_name": "Abuse Elevation Control Mechanism", "tactic": "Privilege Escalation", "description": "Execute commands with elevated root privileges."}
    elif cmd_base in ("crontab", "systemctl"):
        return {"technique_id": "T1053", "technique_name": "Scheduled Task/Job", "tactic": "Persistence", "description": "Configure cron jobs or system services for persistence."}
    elif cmd_base in ("nc", "netcat", "socat", "ncat"):
        return {"technique_id": "T1095", "technique_name": "Non-Application Layer Protocol", "tactic": "Command and Control", "description": "Establish raw socket network connections."}
    elif "history -c" in cmd_full or "rm" in cmd_base:
        return {"technique_id": "T1070", "technique_name": "Indicator Removal", "tactic": "Defense Evasion", "description": "Clear command history or log files to evade detection."}
    return None


def get_full_mitre_matrix():
    """
    Get full MITRE ATT&CK Matrix layout with populated techniques for SOC dashboard.
    """
    mapping = _load_mitre_mapping()
    matrix = {tactic["name"]: [] for tactic in FULL_MITRE_TACTICS}

    # Populate techniques per tactic
    tactic_techs = {}
    for known_cmd, tech in mapping.items():
        tactic = tech.get("tactic", "Discovery")
        tid = tech.get("technique_id")
        tname = tech.get("technique_name")

        if tactic not in tactic_techs:
            tactic_techs[tactic] = {}

        tactic_techs[tactic][tid] = {
            "technique_id": tid,
            "technique_name": tname,
            "description": tech.get("description", "")
        }

    for tactic_name, techs_dict in tactic_techs.items():
        if tactic_name in matrix:
            matrix[tactic_name] = list(techs_dict.values())

    return {
        "tactics": FULL_MITRE_TACTICS,
        "matrix": matrix
    }
