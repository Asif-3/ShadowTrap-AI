"""
ShadowTrap AI - Adaptive Deception Service
=============================================
Generates fake files, folders, credentials, databases, and services
based on attacker behavior patterns to extend engagement and collect
additional intelligence.
"""

import json
import os
import random
from app.utils.logger import get_logger

logger = get_logger("services.deception")

_templates = None


def _load_templates():
    """Load deception templates from JSON file."""
    global _templates
    if _templates is not None:
        return _templates
    
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "deception_templates.json"
    )
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            _templates = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load deception templates: {e}")
        _templates = {"fake_files": {}, "fake_services": [], "fake_credentials": [], "fake_databases": []}
    
    return _templates


def generate_deception_assets(intent, attack_stage, commands):
    """
    Generate adaptive deception assets based on attacker behavior.
    
    Selects appropriate fake data to present to attackers based on
    their detected intent and current attack stage.
    
    Args:
        intent: Detected attacker intent string
        attack_stage: Current attack stage string
        commands: List of command strings
        
    Returns:
        dict: {
            "fake_files": list of fake file paths and content,
            "fake_credentials": list of fake credentials,
            "fake_services": list of fake service banners,
            "fake_databases": list of fake database info,
            "strategy": str describing deception strategy
        }
    """
    templates = _load_templates()
    cmd_text = " ".join(commands).lower()
    
    assets = {
        "fake_files": [],
        "fake_credentials": [],
        "fake_services": [],
        "fake_databases": [],
        "strategy": "",
    }
    
    # Select deception strategy based on intent
    if "credential" in intent.lower() or "credential" in attack_stage.lower():
        assets["strategy"] = "Credential Honeytrap: Deploying fake credentials to track harvesting"
        assets["fake_files"] = templates.get("fake_files", {}).get("credential_theft", [])
        assets["fake_credentials"] = templates.get("fake_credentials", [])
    
    elif "data" in intent.lower() or "exfiltration" in attack_stage.lower():
        assets["strategy"] = "Data Decoy: Providing fake sensitive data to track exfiltration"
        assets["fake_files"] = templates.get("fake_files", {}).get("data_theft", [])
        assets["fake_databases"] = templates.get("fake_databases", [])
    
    elif "persistence" in intent.lower() or "persistence" in attack_stage.lower():
        assets["strategy"] = "Persistence Trap: Allowing fake persistence mechanisms"
        assets["fake_files"] = templates.get("fake_files", {}).get("persistence", [])
        assets["fake_services"] = templates.get("fake_services", [])
    
    elif "reconnaissance" in intent.lower() or "discovery" in attack_stage.lower():
        assets["strategy"] = "Reconnaissance Feed: Providing fake network topology"
        assets["fake_files"] = templates.get("fake_files", {}).get("reconnaissance", [])
        assets["fake_services"] = random.sample(
            templates.get("fake_services", []),
            min(3, len(templates.get("fake_services", [])))
        )
    
    elif "malware" in intent.lower() or "payload" in attack_stage.lower():
        assets["strategy"] = "Malware Sandbox: Isolating payload execution for analysis"
        assets["fake_services"] = templates.get("fake_services", [])
        assets["fake_credentials"] = random.sample(
            templates.get("fake_credentials", []),
            min(2, len(templates.get("fake_credentials", [])))
        )
    
    else:
        assets["strategy"] = "General Deception: Deploying mixed honeytrap assets"
        all_files = []
        for category in templates.get("fake_files", {}).values():
            all_files.extend(category)
        assets["fake_files"] = random.sample(all_files, min(3, len(all_files)))
        assets["fake_credentials"] = random.sample(
            templates.get("fake_credentials", []),
            min(2, len(templates.get("fake_credentials", [])))
        )
    
    logger.info(f"Deception assets generated: strategy={assets['strategy']}")
    return assets
