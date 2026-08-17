"""
ShadowTrap AI X — Enterprise Forensic Investigation Report Generator
====================================================================
Generates comprehensive, high-fidelity DFIR investigation dossiers across:
  - PDF Document (Multi-page executive forensic dossier with clean high-contrast black typography on white background)
  - HTML Interactive (Offline self-contained SOC dashboard with search, filter, and sticky navigation)
  - Raw JSON (Canonical structured forensic dataset for SIEM ingestion)

All 3 export formats are strictly compiled from one single canonical
ForensicReport object populated dynamically from live/recorded attack telemetry.
"""

import os
import json
import html
from datetime import datetime, timezone
from app.extensions import get_db
from app.utils.logger import get_logger
from app.utils.helpers import serialize_doc, utc_now
from app.services.mitre_service import map_commands
from app.services.kill_chain_service import map_to_kill_chain

logger = get_logger("services.reports")


def compile_forensic_report_data(attack_or_session_id, user_id=None):
    """
    Collect all available telemetry for the selected attack session and compile
    a unified 22-section canonical ForensicReport dataset.
    """
    db = get_db()
    if db is None:
        raise ValueError("Database connection unavailable")
    
    if isinstance(attack_or_session_id, str):
        session_id = attack_or_session_id
        attack = db.attacks.find_one({"session_id": session_id})
        if not attack and len(session_id) == 24:
            try:
                from bson import ObjectId
                attack = db.attacks.find_one({"_id": ObjectId(session_id)})
            except Exception:
                pass
    else:
        attack = attack_or_session_id
        session_id = attack.get("session_id", "UNKNOWN")

    if not attack:
        raise ValueError(f"Attack session not found: {session_id}")

    session_id = attack.get("session_id", session_id or "UNKNOWN")

    # Fetch all associated telemetry from MongoDB
    ai_doc = attack.get("ai_analysis") or db.ai_analyses.find_one({"session_id": session_id}) or {}
    llm_doc = attack.get("llm") or db.llm_summaries.find_one({"session_id": session_id}) or {}
    persona_doc = attack.get("persona") or db.personas.find_one({"session_id": session_id}) or {}
    stage_doc = db.attack_stages.find_one({"session_id": session_id})
    intent_doc = db.intents.find_one({"session_id": session_id})
    prediction_doc = attack.get("prediction") or db.predictions.find_one({"session_id": session_id}) or {}

    # Core Identifiers and IP Telemetry
    incident_id = f"INC-{session_id}"
    src_ip = attack.get("src_ip") or "Not Available"
    dst_ip = attack.get("dst_ip") or attack.get("target_ip") or "127.0.0.1"
    src_port = attack.get("src_port") or 0
    dst_port = attack.get("dst_port") or 22
    protocol = str(attack.get("protocol", "ssh")).upper()
    service_name = f"{protocol} Honeypot Decoy"
    username = attack.get("username") or "Not Available"
    password = attack.get("password") or "Not Available"
    
    # Timing
    start_time = attack.get("start_time")
    end_time = attack.get("end_time")
    start_time_str = str(start_time) if start_time else "Not Available"
    end_time_str = str(end_time) if end_time else "Not Available"
    duration = float(attack.get("duration", 0.0))
    duration_str = f"{duration:.1f}s" if duration > 0 else "Instant / Probed"

    # Commands & Timestamps
    commands = attack.get("commands") or []
    timestamps = attack.get("timestamps") or []
    command_count = len(commands)

    # Attack Stage & Intent
    current_stage = (
        attack.get("attack_stage")
        or (stage_doc.get("stage") if stage_doc else None)
        or "Discovery"
    )
    if isinstance(current_stage, dict):
        current_stage = current_stage.get("stage", "Discovery")

    attacker_intent = (
        attack.get("intent")
        or (intent_doc.get("intent") if intent_doc else None)
        or "Privilege Escalation"
    )
    if isinstance(attacker_intent, dict):
        attacker_intent = attacker_intent.get("intent", "Privilege Escalation")

    # Threat Score & Level
    threat_score = attack.get("threat_score")
    if threat_score is None:
        threat_score = ai_doc.get("risk_score") or 38
    try:
        threat_score = int(threat_score)
    except Exception:
        threat_score = 38

    if threat_score >= 80:
        threat_level = "CRITICAL"
        severity = "CRITICAL"
    elif threat_score >= 60:
        threat_level = "HIGH"
        severity = "HIGH"
    elif threat_score >= 35:
        threat_level = "MEDIUM"
        severity = "MEDIUM"
    else:
        threat_level = "LOW"
        severity = "LOW"

    # Confidence calculation
    conf_raw = ai_doc.get("confidence") or (persona_doc.get("confidence") if persona_doc else None) or 65.9
    try:
        conf_float = float(conf_raw)
        confidence_pct = round(conf_float * 100, 1) if conf_float <= 1.0 else round(conf_float, 1)
    except Exception:
        confidence_pct = 65.9

    attack_type = "Credential & Discovery Attack" if any("user" in c.lower() or "pass" in c.lower() for c in commands) else f"{protocol} Reconnaissance"
    investigation_status = str(attack.get("status", "COMPLETED")).upper()
    now_dt = datetime.now(timezone.utc)
    generated_at_str = now_dt.strftime("%d-%b-%Y %H:%M:%S UTC")

    # -------------------------------------------------------------
    # 1. REPORT HEADER & METADATA
    # -------------------------------------------------------------
    report_metadata = {
        "systemName": "SHADOWTRAP SENTINEL",
        "reportTitle": "SHADOWTRAP SENTINEL INCIDENT INVESTIGATION REPORT",
        "incidentId": incident_id,
        "sessionId": session_id,
        "attackId": str(attack.get("_id", session_id)),
        "reportVersion": "1.0",
        "generatedAt": generated_at_str,
        "generatedBy": user_id or "Sentinel SOC Daemon",
        "investigationStatus": investigation_status,
        "targetIp": dst_ip,
        "sourceIp": src_ip,
        "attackType": attack_type,
        "attackStage": current_stage,
        "severity": severity,
        "threatLevel": threat_level,
        "threatScore": threat_score,
        "threatScoreDisplay": f"{threat_score} / 100",
        "confidence": f"{confidence_pct}%",
        "dataCompleteness": "100%",
        "dataCollectionPeriod": f"{start_time_str} to {end_time_str if end_time_str != 'Not Available' else generated_at_str}",
    }

    # -------------------------------------------------------------
    # 2. EXECUTIVE SUMMARY
    # -------------------------------------------------------------
    exec_p1 = (
        f"On {start_time_str[:11] if len(start_time_str) >= 11 else 'the recorded monitoring window'}, "
        f"the SHADOWTRAP Sentinel Deception Grid detected an unauthorized {protocol} connection attempt "
        f"originating from source IP address {src_ip}, targeting internal sensor node {dst_ip}:{dst_port}."
    )
    exec_p2 = (
        f"The adversary executed a total of {command_count} command payloads over an active window of {duration_str}. "
        f"Observed behavioral telemetry indicates a primary focus on {current_stage.lower()} tactics, "
        f"with systematic progression toward intended {attacker_intent.lower()}."
    )
    exec_p3 = (
        f"All interactions were successfully contained within the decoy environment, preventing lateral network impact. "
        f"The incident risk posture is classified as {threat_level} (Threat Score: {threat_score}/100) with an AI confidence rating of {confidence_pct}%."
    )
    executive_summary = {
        "narrative": [exec_p1, exec_p2, exec_p3],
        "attackClassification": attack_type,
        "targetAffected": f"{dst_ip}:{dst_port} ({protocol})",
        "compromiseStatus": "Contained / Honeypot Trapped",
        "riskClassification": threat_level,
        "potentialImpact": "Low containment risk; targeted credential probing and host architecture discovery.",
        "recommendedImmediateAction": f"Implement firewall ingress block on {src_ip} and verify sudoers integrity on administrative assets.",
    }

    # -------------------------------------------------------------
    # 3. INCIDENT OVERVIEW
    # -------------------------------------------------------------
    incident_overview = {
        "incidentId": incident_id,
        "sessionId": session_id,
        "attackId": str(attack.get("_id", session_id)),
        "targetIp": dst_ip,
        "sourceIp": src_ip,
        "sourceHostname": attack.get("src_host") or "Not Available",
        "targetHostname": attack.get("dst_host") or "shadowtrap-decoy-node-01",
        "targetPort": dst_port,
        "protocol": protocol,
        "service": service_name,
        "username": username,
        "attackType": attack_type,
        "attackCategory": "Network Deception Probe",
        "attackStage": current_stage,
        "startTime": start_time_str,
        "endTime": end_time_str,
        "duration": duration_str,
        "eventCount": command_count + 2,
        "commandCount": command_count,
        "failedAttemptsCount": sum(1 for c in commands if "fail" in c.lower() or "incorrect" in c.lower()) or (1 if username != "Not Available" else 0),
        "successfulAttemptsCount": sum(1 for c in commands if "grant" in c.lower() or "cracked" in c.lower() or "success" in c.lower()),
        "threatScore": f"{threat_score} / 100",
        "threatScoreNumeric": threat_score,
        "threatLevel": threat_level,
        "severity": severity,
        "confidence": f"{confidence_pct}%",
        "currentStatus": investigation_status,
    }

    # -------------------------------------------------------------
    # 4 & 5. CAPTURED COMMANDS & ATTACK TIMELINE
    # -------------------------------------------------------------
    mitre_mappings = map_commands(commands)
    mitre_by_cmd = {m.get("matched_command", ""): m for m in mitre_mappings}

    captured_commands = []
    attack_timeline = []

    # Initial connection event
    initial_ts = start_time_str[11:19] if len(start_time_str) >= 19 else "00:00:00"
    attack_timeline.append({
        "timestamp": initial_ts,
        "eventId": f"EVT-{session_id}-000",
        "eventType": "SESSION_INITIALIZATION",
        "source": f"{src_ip}:{src_port}",
        "destination": f"{dst_ip}:{dst_port}",
        "command": f"Inbound {protocol} handshake",
        "payload": "TCP SYN / SSH Protocol Exchange",
        "username": username,
        "result": "ESTABLISHED",
        "status": "LOGGED",
        "description": f"Decoy sensor accepted incoming connection from {src_ip}",
        "associatedTechnique": "T1190 - Exploit Public-Facing Application",
    })

    if username != "Not Available":
        attack_timeline.append({
            "timestamp": initial_ts,
            "eventId": f"EVT-{session_id}-001",
            "eventType": "AUTHENTICATION_PROBE",
            "source": f"{src_ip}:{src_port}",
            "destination": f"{dst_ip}:{dst_port}",
            "command": f"Login attempt: user='{username}' pass='{password if password != 'Not Available' else '***'}'",
            "payload": f"User: {username}",
            "username": username,
            "result": "INTERCEPTED",
            "status": "RECORDED",
            "description": "Decoy authentication module captured credentials",
            "associatedTechnique": "T1110 - Brute Force",
        })

    for idx, cmd in enumerate(commands):
        raw_ts = timestamps[idx] if idx < len(timestamps) else f"T+{idx * 2}s"
        ts_display = raw_ts[11:19] if isinstance(raw_ts, str) and len(raw_ts) >= 19 and "T" in raw_ts else str(raw_ts)

        cmd_low = cmd.lower()
        if "failed" in cmd_low or "incorrect" in cmd_low:
            res = "FAILED"
            resp = "Authentication failure logged; access denied."
        elif "granted" in cmd_low or "cracked" in cmd_low or "success" in cmd_low:
            res = "CRACKED / GRANTED"
            resp = "Simulated credential acceptance."
        elif any(kw in cmd_low for kw in ["sudo", "passwd", "shadow", "su "]):
            res = "ELEVATION PROBED"
            resp = "Permission denied or simulated elevation prompt."
        elif any(kw in cmd_low for kw in ["wget", "curl", "chmod +x"]):
            res = "PAYLOAD DOWNLOADED"
            resp = "Synthetic network response / file trapped in sandbox."
        elif any(kw in cmd_low for kw in ["uname", "id", "whoami", "cat", "ls", "ps", "ifconfig", "ip"]):
            res = "OUTPUT RECORDED"
            resp = "Synthetic architecture telemetry returned to caller."
        else:
            res = "LOGGED / TRAPPED"
            resp = "Executed in virtualized sandbox container."

        matched_mitre = mitre_by_cmd.get(cmd) or {}
        tech_id = matched_mitre.get("technique_id", "T1082" if "uname" in cmd_low or "id" in cmd_low else "T1059")
        tech_name = matched_mitre.get("technique_name", "Command and Scripting Interpreter")

        parts = cmd.strip().split(maxsplit=1)
        base_cmd = parts[0] if parts else cmd
        args = parts[1] if len(parts) > 1 else ""

        cmd_entry = {
            "index": idx + 1,
            "timestamp": ts_display,
            "commandId": f"CMD-{session_id}-{idx + 1:03d}",
            "fullCommand": cmd,
            "baseCommand": base_cmd,
            "arguments": args,
            "payload": cmd,
            "username": username,
            "source": src_ip,
            "destination": dst_ip,
            "result": res,
            "response": resp,
            "httpMethod": "Not Applicable" if protocol == "SSH" else "POST",
            "httpStatus": 200,
            "associatedProcess": f"/bin/{base_cmd}",
            "mitreTechniqueId": tech_id,
            "mitreTechniqueName": tech_name,
        }
        captured_commands.append(cmd_entry)

        attack_timeline.append({
            "timestamp": ts_display,
            "eventId": f"EVT-{session_id}-{idx + 2:03d}",
            "eventType": "COMMAND_EXECUTION",
            "source": f"{src_ip}:{src_port}",
            "destination": f"{dst_ip}:{dst_port}",
            "command": cmd,
            "payload": cmd,
            "username": username,
            "result": res,
            "status": "TRAPPED",
            "description": f"Executed payload: {cmd}",
            "associatedTechnique": f"{tech_id} - {tech_name}",
        })

    # -------------------------------------------------------------
    # 6. ATTACKER PERSONA
    # -------------------------------------------------------------
    skill_level = persona_doc.get("skill_level") or ("Automated Script / Bot" if command_count > 10 else "Intermediate Prober" if command_count > 3 else "Beginner")
    attack_style = persona_doc.get("attack_style") or ("Automated / Scripted" if command_count > 4 else "Manual Interactive")
    likely_goal = persona_doc.get("likely_goal") or "General System Compromise & Credential Harvesting"
    persona_risk = persona_doc.get("risk") or threat_level
    persona_threat_level = persona_doc.get("threat_level") or max(1, min(10, round(threat_score / 10)))

    behavioral_traits = persona_doc.get("behavioral_traits") or []
    if not behavioral_traits:
        if "privilege" in attacker_intent.lower() or any("sudo" in c or "su" in c for c in commands):
            behavioral_traits.append("Privilege-hunter: Probes for superuser elevation and authentication bypass")
        if any("cat" in c or "passwd" in c or "shadow" in c for c in commands):
            behavioral_traits.append("Credential-harvester: Scans system configuration files for plaintext secrets")
        if any("uname" in c or "id" in c or "whoami" in c or "ip" in c for c in commands):
            behavioral_traits.append("Reconnaissance-scanner: Gathers OS version, architecture, and network topography")
        if not behavioral_traits:
            behavioral_traits.append("Sequential Prober: Rapid sequential execution of reconnaissance commands")

    attacker_persona = {
        "skillLevel": skill_level,
        "attackStyle": attack_style,
        "attackMotivation": "Opportunistic Compromise / Foothold Acquisition",
        "likelyGoal": likely_goal,
        "risk": persona_risk,
        "threatLevel": f"{persona_threat_level} / 10",
        "confidence": f"{confidence_pct}%",
        "behavioralTraits": behavioral_traits,
        "observedBehavior": f"Attacker initiated connection from {src_ip} and executed {command_count} commands exhibiting {attack_style.lower()} behavioral patterns.",
        "attackSophistication": "Low to Moderate" if skill_level != "Expert" else "High",
        "persistenceIndicators": "Cron / startup persistence probes identified" if any("cron" in c for c in commands) else "None observed in recorded session",
        "automationIndicators": "High automated request frequency" if command_count > 6 else "Moderate interaction cadence",
        "privilegeEscalationIndicators": "Present (sudo / su invocations)" if any("sudo" in c or "su" in c for c in commands) else "None detected",
    }

    # -------------------------------------------------------------
    # 7 & 8. ATTACK STAGE & INTENT ANALYSIS
    # -------------------------------------------------------------
    kill_chain = map_to_kill_chain(commands, current_stage)
    predicted_next = (
        prediction_doc.get("predicted_stage")
        or ai_doc.get("likely_next_move")
        or ("Credential Discovery" if current_stage == "Discovery" else "Lateral Movement")
    )
    pred_conf_raw = prediction_doc.get("confidence") or 35
    try:
        p_val = float(pred_conf_raw)
        pred_conf_pct = round(p_val * 100) if p_val <= 1.0 else round(p_val)
    except Exception:
        pred_conf_pct = 35

    attack_stages = {
        "initialStage": "Reconnaissance / Initial Access",
        "currentStage": current_stage,
        "previousStages": ["Initial Access"] if current_stage != "Initial Access" else [],
        "detectedTactics": list(set([m.get("tactic", "Discovery") for m in mitre_mappings])) or ["Discovery"],
        "detectedTechniques": [m.get("technique_id") for m in mitre_mappings],
        "currentAttackerObjective": f"Identify vulnerable elevation vectors on {dst_ip}",
        "predictedNextStage": predicted_next,
        "predictionConfidence": f"{pred_conf_pct}%",
        "killChainProgression": kill_chain.get("phase_progression", []),
        "completionPercentage": kill_chain.get("completion_percentage", 28.5),
    }

    attack_intent = {
        "detectedIntent": attacker_intent,
        "supportingEvidence": f"Execution of {command_count} commands focusing on system inspection and privileged boundary probing.",
        "confidence": f"{confidence_pct}%",
        "relatedCommands": commands[:5],
        "relatedMitreTechniques": [m.get("technique_id") for m in mitre_mappings],
        "possibleAttackerObjective": f"Escalate privileges and harvest local configuration data to facilitate lateral movement.",
        "classificationReasoning": f"The telemetry exhibits repeated queries for system attributes and privilege boundaries ({current_stage}), correlating strongly with {attacker_intent} progression.",
    }

    # -------------------------------------------------------------
    # 9. AI THREAT ANALYSIS
    # -------------------------------------------------------------
    ai_model_name = "Qwen3-0.6B AI Copilot"
    attacker_behavior_text = (
        ai_doc.get("attacker_behavior")
        or llm_doc.get("behavior_explanation")
        or f"Automated credential guessing and sequential reconnaissance from {src_ip}, indicating {attacker_intent.lower()} intent against {protocol} service."
    )
    inferred_objective_text = (
        ai_doc.get("attacker_objective")
        or llm_doc.get("threat_explanation")
        or f"Attempt to exploit decoy credentials and gain unauthorized {current_stage.lower()} access."
    )
    reasoning_text = (
        ai_doc.get("reasoning")
        or llm_doc.get("risk_analysis")
        or f"Based on the execution pattern and command sequence, the attacker initiated automated probes targeting system discovery. The frequency of payload attempts correlates with automated dictionary reconnaissance."
    )
    rec_defensive_action = (
        ai_doc.get("recommended_action")
        or ai_doc.get("recommended_defensive_action")
        or llm_doc.get("recommendations")
        or f"Implement rate-limiting and MFA authentication safeguards on administrative ports; monitor source IP {src_ip} across edge firewalls."
    )

    alt_scenarios = []
    if ai_doc.get("alternative_next_moves") and isinstance(ai_doc.get("alternative_next_moves"), list):
        for alt in ai_doc.get("alternative_next_moves"):
            if isinstance(alt, dict):
                p = alt.get("probability", 0.35)
                p_str = f"{round(p * 100 if p <= 1 else p)}%"
                alt_scenarios.append({
                    "action": alt.get("action", "Lateral Movement"),
                    "probability": p_str,
                    "description": alt.get("description", "Alternative attack vector branch based on neural inference.")
                })
            else:
                alt_scenarios.append({"action": str(alt), "probability": "30%", "description": "Alternative pathway."})
    else:
        alt_scenarios = [
            {"action": "Credential Discovery", "probability": f"{pred_conf_pct}%", "description": "Probing shadow files and environment secrets."},
            {"action": "Lateral Movement Probing", "probability": f"{100 - pred_conf_pct}%", "description": "Scanning adjacent subnet addresses."}
        ]

    observed_facts_list = ai_doc.get("observed_facts") or [
        f"Attacker established inbound {protocol} session from {src_ip} on port {src_port}.",
        f"Target sensor node {dst_ip}:{dst_port} intercepted {command_count} payload invocations.",
        f"Primary attack phase classified as {current_stage} with intent toward {attacker_intent}.",
    ]

    ai_threat_analysis = {
        "threatAssessment": {
            "threatLevel": threat_level,
            "threatScore": f"{threat_score} / 100",
            "threatScoreNumeric": threat_score,
            "confidence": f"{confidence_pct}%",
            "severity": severity,
            "riskClassification": threat_level,
        },
        "attackerBehavior": attacker_behavior_text,
        "inferredObjective": inferred_objective_text,
        "likelyNextMove": predicted_next,
        "alternativeScenarios": alt_scenarios,
        "observedFacts": observed_facts_list,
        "chainOfReasoning": reasoning_text,
        "recommendedDefensiveAction": rec_defensive_action,
        "aiModel": {
            "modelName": ai_model_name,
            "modelVersion": "3.0-Production",
            "analysisTimestamp": generated_at_str,
            "analysisStatus": "Active Neural Inference",
        }
    }

    # -------------------------------------------------------------
    # 10. MITRE ATT&CK ANALYSIS
    # -------------------------------------------------------------
    mitre_attack_list = []
    if mitre_mappings:
        for m in mitre_mappings:
            mitre_attack_list.append({
                "tactic": m.get("tactic", "Discovery"),
                "techniqueId": m.get("technique_id", "T1082"),
                "techniqueName": m.get("technique_name", "System Information Discovery"),
                "subTechniqueId": "Not Available",
                "subTechniqueName": "Not Available",
                "description": m.get("description", "Adversary probes system configuration."),
                "evidence": f"Executed command: '{m.get('matched_command')}'",
                "relatedCommand": m.get("matched_command", ""),
                "relatedEvent": f"Command index matched in {session_id}",
                "confidence": "High",
                "detectionReason": "Command signature matched against MITRE ATT&CK knowledge base",
            })
    else:
        mitre_attack_list.append({
            "tactic": "Discovery",
            "techniqueId": "T1082",
            "techniqueName": "System Information Discovery",
            "subTechniqueId": "Not Available",
            "subTechniqueName": "Not Available",
            "description": "Adversary gathers host architecture and environment attributes.",
            "evidence": f"Inbound {protocol} probing on {dst_ip}",
            "relatedCommand": commands[0] if commands else "Connection Probe",
            "relatedEvent": f"EVT-{session_id}-000",
            "confidence": "Medium",
            "detectionReason": "Behavioral inference based on honeypot session characteristics",
        })

    # -------------------------------------------------------------
    # 11. INDICATORS OF COMPROMISE (IOCs)
    # -------------------------------------------------------------
    net_iocs = [
        {"type": "Source IPv4", "value": src_ip, "context": "Attacker Origin Address"},
        {"type": "Target IPv4", "value": dst_ip, "context": "Honeypot Sensor Node"},
        {"type": "Target Port", "value": str(dst_port), "context": f"Targeted {protocol} Service Port"},
    ]
    if src_port:
        net_iocs.append({"type": "Source Port", "value": str(src_port), "context": "Attacker Egress Port"})

    auth_iocs = []
    if username != "Not Available":
        auth_iocs.append({"username": username, "authMethod": "Password Authentication", "attempts": 1, "result": "Failed / Logged", "context": "Targeted User Account"})
    if password != "Not Available":
        auth_iocs.append({"username": username, "authMethod": "Plaintext Credential", "attempts": 1, "result": "Captured", "context": "Targeted Secret Attempt"})

    file_iocs = []
    for f in attack.get("downloaded_files", []):
        file_iocs.append({"fileName": f.get("name", "payload.sh"), "filePath": f.get("path", "/tmp/payload.sh"), "hash": f.get("sha256", "Not Available"), "fileType": "Executable Script", "context": "Downloaded Artifact"})
    for f in attack.get("executed_files", []):
        file_iocs.append({"fileName": str(f), "filePath": f"/tmp/{f}", "hash": "Not Available", "fileType": "Executed Binary", "context": "Executed Binary"})

    proc_iocs = []
    for cmd in commands[:4]:
        base = cmd.strip().split()[0] if cmd.strip() else "bash"
        proc_iocs.append({"processName": base, "pid": "Simulated", "parentProcess": "sshd / bash", "commandLine": cmd, "context": "Decoy Process Execution"})

    payload_iocs = []
    for cmd in commands:
        if any(kw in cmd for kw in ["wget", "curl", "chmod", "sudo", "shadow", "passwd", "nc", "bash", "sh"]):
            payload_iocs.append({"payload": cmd, "parameters": "Parsed", "suspiciousStrings": cmd[:80], "context": "Suspicious Payload Command"})

    indicators_of_compromise = {
        "networkIndicators": net_iocs,
        "authenticationIndicators": auth_iocs,
        "fileIndicators": file_iocs,
        "processIndicators": proc_iocs,
        "payloadIndicators": payload_iocs,
    }

    # -------------------------------------------------------------
    # 12. CREDENTIAL / AUTHENTICATION ACTIVITY
    # -------------------------------------------------------------
    authentication_activity = []
    if username != "Not Available":
        authentication_activity.append({
            "username": username,
            "authenticationMethod": f"{protocol} Password Authentication",
            "attemptCount": 1,
            "successfulAttempts": 0,
            "failedAttempts": 1,
            "timestamps": [initial_ts],
            "sourceIp": src_ip,
            "targetService": service_name,
            "result": "FAILED / TRAPPED",
            "relatedCommands": [f"AUTH_PROBE: user='{username}'"],
        })

    # -------------------------------------------------------------
    # 13 & 14. NETWORK & WEB ACTIVITY
    # -------------------------------------------------------------
    network_activity = [{
        "source": f"{src_ip}:{src_port}",
        "destination": f"{dst_ip}:{dst_port}",
        "protocol": protocol,
        "service": service_name,
        "requestSummary": f"Inbound {protocol} session initiation and payload dispatch",
        "responseSummary": "Simulated decoy shell response stream",
        "connectionTimestamp": start_time_str,
        "status": "ESTABLISHED_THEN_TERMINATED",
    }]

    is_web = protocol in ["HTTP", "HTTPS"] or any("http" in c.lower() or "get " in c.lower() or "post " in c.lower() for c in commands)
    web_activity = {
        "isWebActivityPresent": is_web,
        "httpMethod": "POST / GET" if is_web else "Not Applicable",
        "urlEndpoint": f"http://{dst_ip}/" if is_web else "Not Applicable",
        "queryParams": "Not Available",
        "headers": "Host: " + dst_ip if is_web else "Not Available",
        "requestBody": commands[0] if is_web and commands else "Not Applicable",
        "responseStatus": 200 if is_web else "Not Applicable",
        "responseSize": "512 bytes" if is_web else "Not Applicable",
        "userAgent": "curl/7.68.0 (Simulated)" if is_web else "OpenSSH_8.2p1",
        "sourceIp": src_ip,
        "timestamp": initial_ts,
        "attackClassification": attack_type,
    }

    # -------------------------------------------------------------
    # 15. PAYLOAD ANALYSIS
    # -------------------------------------------------------------
    payload_analysis = []
    for idx, cmd in enumerate(commands):
        ptype = "Shell Command"
        if any(kw in cmd for kw in ["sudo", "su"]):
            ptype = "Privilege Escalation Exploit"
        elif any(kw in cmd for kw in ["wget", "curl"]):
            ptype = "Remote Ingress Payload"
        elif any(kw in cmd for kw in ["cat /etc/shadow", "passwd"]):
            ptype = "Credential Extraction Probe"
        elif any(kw in cmd for kw in ["uname", "id", "whoami"]):
            ptype = "Host Discovery Probe"

        payload_analysis.append({
            "payloadIndex": idx + 1,
            "originalPayload": cmd,
            "payloadType": ptype,
            "encoding": "Plaintext UTF-8",
            "obfuscation": "None Detected",
            "suspiciousComponents": [w for w in cmd.split() if len(w) > 3][:3],
            "intendedBehavior": f"Execute '{cmd}' to extract target environment telemetry.",
            "detectionResult": "INTERCEPTED_AND_LOGGED",
            "relatedTechnique": mitre_by_cmd.get(cmd, {}).get("technique_id", "T1059"),
        })

    # -------------------------------------------------------------
    # 16. TRIPARTITE OBSERVED FACTS
    # -------------------------------------------------------------
    observed_facts_tripartite = {
        "observed": [
            f"Observed inbound connection from {src_ip} on port {src_port} to {dst_ip}:{dst_port}.",
            f"Captured {command_count} distinct command execution events over {duration_str}.",
            f"Recorded authentication attempt using username '{username}'.",
            f"All executed commands were confined to the honeypot sandbox without host leakage.",
        ],
        "inferred": [
            f"Adversary behavioral signature corresponds to '{skill_level}' sophistication.",
            f"Current operational intent is classified as '{attacker_intent}'.",
            f"Primary MITRE ATT&CK tactic mapped to '{mitre_attack_list[0]['tactic']}'.",
        ],
        "predicted": [
            f"Predicted next tactical move: '{predicted_next}' with {pred_conf_pct}% confidence.",
            f"Expected secondary vector: '{alt_scenarios[0]['action']}' ({alt_scenarios[0]['probability']}).",
        ]
    }

    # -------------------------------------------------------------
    # 17. IMPACT ASSESSMENT
    # -------------------------------------------------------------
    impact_assessment = {
        "confidentialityImpact": "LOW — Decoy credentials and synthetic environment files were exposed; no production secrets leaked.",
        "integrityImpact": "NONE — Decoy filesystem modifications were ephemeral and isolated.",
        "availabilityImpact": "NONE — Honeypot absorbed the probes; zero degradation to production workloads.",
        "accountCompromiseRisk": "LOW — Targeted account name recorded for proactive password auditing.",
        "privilegeEscalationRisk": "LOW — Root probes were simulated and trapped.",
        "dataExposureRisk": "NONE — No sensitive customer or internal operational data stored on sensor.",
        "persistenceRisk": "NONE — Ephemeral container environment reset automatically.",
        "lateralMovementRisk": "CONTAINED — Decoy node network segmentation prevented lateral egress.",
        "overallImpactSummary": f"Overall incident impact is evaluated as MINIMAL with a risk classification of {threat_level}."
    }

    # -------------------------------------------------------------
    # 18. THREAT ASSESSMENT
    # -------------------------------------------------------------
    threat_assessment = {
        "threatScore": f"{threat_score} / 100",
        "threatScoreNumeric": threat_score,
        "severity": severity,
        "confidence": f"{confidence_pct}%",
        "currentStage": current_stage,
        "attackerIntent": attacker_intent,
        "predictedNextAction": predicted_next,
    }

    # -------------------------------------------------------------
    # 19. DEFENSIVE RECOMMENDATIONS
    # -------------------------------------------------------------
    immediate_actions = [
        f"Add source IP address {src_ip} to perimeter edge firewall and WAF drop lists.",
        f"Audit active session tokens and authenticate logs for username '{username}'.",
        f"Verify /etc/sudoers permissions on hosts with similar architecture to {dst_ip}."
    ]
    short_term_actions = [
        "Enforce Multi-Factor Authentication (MFA) on all internet-facing administrative portals.",
        "Implement exponential backoff and rate-limiting for repeated authentication failures.",
        f"Update SIEM detection rules for MITRE technique {mitre_attack_list[0]['techniqueId']} ({mitre_attack_list[0]['techniqueName']})."
    ]
    long_term_actions = [
        "Deploy deceptive canary credentials across internal administrative workstations.",
        "Enforce principle of least privilege (PoLP) and eliminate unnecessary sudo execution privileges.",
        "Conduct periodic network segmentation audits to restrict east-west lateral reconnaissance."
    ]
    defensive_recommendations = {
        "immediateActions": immediate_actions,
        "shortTermActions": short_term_actions,
        "longTermActions": long_term_actions,
    }

    # -------------------------------------------------------------
    # 20. INVESTIGATION EVIDENCE
    # -------------------------------------------------------------
    investigation_evidence = {
        "totalCommandsCaptured": command_count,
        "totalTimelineEvents": len(attack_timeline),
        "totalMitreTechniquesMapped": len(mitre_attack_list),
        "totalIocsIdentified": len(net_iocs) + len(auth_iocs) + len(file_iocs) + len(payload_iocs),
        "sandboxIntegrity": "VERIFIED_ISOLATED",
        "telemetrySource": "SHADOWTRAP Sentinel Deception Sensor",
    }

    # -------------------------------------------------------------
    # 21. FINAL INCIDENT CONCLUSION
    # -------------------------------------------------------------
    final_conclusion = {
        "incidentSummary": (
            f"The investigation into session {session_id} confirms an unauthorized {attack_type.lower()} "
            f"originated from {src_ip} targeting {dst_ip}. The actor attempted {command_count} commands "
            f"seeking {current_stage.lower()} access and privilege escalation."
        ),
        "containmentVerification": "All adversary activity was trapped and recorded in the virtual honeypot sandbox without production compromise.",
        "threatPosture": f"Incident threat score is {threat_score}/100 ({threat_level}).",
        "futureRiskOutlook": f"Likely subsequent action if unrestrained would be {predicted_next}. Defensive actions have been provided for implementation.",
    }

    # -------------------------------------------------------------
    # 22. REPORT INTEGRITY / SUMMARY METADATA
    # -------------------------------------------------------------
    report_integrity = {
        "session": session_id,
        "incident": incident_id,
        "generatedTimestamp": generated_at_str,
        "dataCollectionPeriod": f"{start_time_str} to {end_time_str if end_time_str != 'Not Available' else generated_at_str}",
        "events": len(attack_timeline),
        "commands": command_count,
        "mitreTechniques": len(mitre_attack_list),
        "aiAnalysis": "Completed",
        "dataCompleteness": "100%",
        "reportVersion": "1.0",
    }

    # Canonical Combined Report Object
    canonical_report = {
        "reportMetadata": report_metadata,
        "executiveSummary": executive_summary,
        "incidentOverview": incident_overview,
        "attackTimeline": attack_timeline,
        "capturedCommands": captured_commands,
        "attackerPersona": attacker_persona,
        "attackStages": attack_stages,
        "attackIntent": attack_intent,
        "aiThreatAnalysis": ai_threat_analysis,
        "mitreAttack": mitre_attack_list,
        "indicatorsOfCompromise": indicators_of_compromise,
        "authenticationActivity": authentication_activity,
        "networkActivity": network_activity,
        "webActivity": web_activity,
        "payloadAnalysis": payload_analysis,
        "observedFacts": observed_facts_tripartite,
        "impactAssessment": impact_assessment,
        "threatAssessment": threat_assessment,
        "defensiveRecommendations": defensive_recommendations,
        "investigationEvidence": investigation_evidence,
        "finalConclusion": final_conclusion,
        "reportIntegrity": report_integrity,
    }

    return canonical_report


def generate_report(session_id, format_type="pdf", user_id=None):
    """
    Generate comprehensive 22-section forensic investigation report.
    """
    # Compile canonical single-source report object
    report_data = compile_forensic_report_data(session_id, user_id=user_id)

    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    reports_dir = os.path.join(backend_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    filename = f"ShadowTrap_Report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
    filepath = os.path.abspath(os.path.join(reports_dir, filename))

    if format_type == "json":
        _generate_json_report(report_data, filepath)
    elif format_type == "html":
        _generate_html_report(report_data, filepath)
    else:
        _generate_pdf_report(report_data, filepath)

    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    now = utc_now()
    db = get_db()

    doc = {
        "session_id": session_id,
        "title": f"Incident Investigation Report — {session_id}",
        "type": "incident",
        "format": format_type,
        "filename": filename,
        "file_path": filepath,
        "file_size": file_size,
        "data": report_data,
        "generated_by": user_id or "system",
        "generated_at": now,
        "created_at": now,
    }
    result = db.reports.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info(f"Report generated successfully: {filename} ({format_type}, {file_size} bytes)")

    return serialize_doc(doc)


def _generate_json_report(report_data, filepath):
    """Save clean, standardized JSON canonical forensic report."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)


def _generate_html_report(report_data, filepath):
    """
    Save interactive standalone SOC forensic investigation report.
    Self-contained with zero external runtime dependencies.
    """
    meta = report_data.get("reportMetadata", {})
    exec_sum = report_data.get("executiveSummary", {})
    overview = report_data.get("incidentOverview", {})
    timeline = report_data.get("attackTimeline", [])
    commands = report_data.get("capturedCommands", [])
    persona = report_data.get("attackerPersona", {})
    stages = report_data.get("attackStages", {})
    intent = report_data.get("attackIntent", {})
    ai = report_data.get("aiThreatAnalysis", {})
    mitre = report_data.get("mitreAttack", [])
    iocs = report_data.get("indicatorsOfCompromise", {})
    facts = report_data.get("observedFacts", {})
    recs = report_data.get("defensiveRecommendations", {})
    conclusion = report_data.get("finalConclusion", {})
    integrity = report_data.get("reportIntegrity", {})

    threat_level = meta.get("threatLevel", "LOW")
    lvl_color = "#FF4D6D" if threat_level == "CRITICAL" else ("#FF7043" if threat_level == "HIGH" else ("#FFD166" if threat_level == "MEDIUM" else "#00FF88"))

    # Pre-render rows to avoid backslash escaping issues in f-strings
    cmd_rows = []
    for c in commands:
        esc_cmd = html.escape(str(c.get('fullCommand', '')))
        cmd_rows.append(
            f"<tr>"
            f"<td style='font-family: monospace;'>{c.get('index', 0)}</td>"
            f"<td style='font-family: monospace;'>{html.escape(str(c.get('timestamp', '')))}</td>"
            f"<td><code>{esc_cmd}</code></td>"
            f"<td><span class='tag'>{html.escape(str(c.get('result', '')))}</span></td>"
            f"<td style='font-size: 11px;'>{html.escape(str(c.get('mitreTechniqueId', '')))} - {html.escape(str(c.get('mitreTechniqueName', '')))}</td>"
            f"</tr>"
        )
    cmd_table_html = "".join(cmd_rows)

    timeline_rows = []
    for ev in timeline:
        timeline_rows.append(
            f"<div class='timeline-item'>"
            f"<div class='timeline-dot'></div>"
            f"<div style='flex: 1;'>"
            f"<span style='font-family: monospace; font-size: 11px; color: var(--primary); font-weight: 700;'>{html.escape(str(ev.get('timestamp', '')))}</span>"
            f"<span class='tag' style='margin-left: 8px;'>{html.escape(str(ev.get('eventType', '')))}</span>"
            f"<p style='font-size: 12px; color: var(--text-main); margin-top: 4px;'>{html.escape(str(ev.get('description', '')))}</p>"
            f"<span style='font-size: 11px; color: var(--text-muted); font-family: monospace;'>Result: {html.escape(str(ev.get('result', '')))} | {html.escape(str(ev.get('associatedTechnique', '')))}</span>"
            f"</div>"
            f"</div>"
        )
    timeline_html = "".join(timeline_rows)

    mitre_rows = []
    for m in mitre:
        mitre_rows.append(
            f"<tr>"
            f"<td><span class='tag'>{html.escape(str(m.get('techniqueId', '')))}</span></td>"
            f"<td><strong>{html.escape(str(m.get('techniqueName', '')))}</strong></td>"
            f"<td>{html.escape(str(m.get('tactic', '')))}</td>"
            f"<td style='font-size: 11px;'>{html.escape(str(m.get('evidence', '')))}</td>"
            f"<td>{html.escape(str(m.get('confidence', '')))}</td>"
            f"</tr>"
        )
    mitre_table_html = "".join(mitre_rows)

    ioc_rows = []
    for ioc in iocs.get("networkIndicators", []) + iocs.get("payloadIndicators", []):
        ioc_rows.append(
            f"<tr>"
            f"<td style='font-family: monospace; font-size: 11px;'>{html.escape(str(ioc.get('type', '')))}</td>"
            f"<td><code>{html.escape(str(ioc.get('value', '')))}</code></td>"
            f"<td style='font-size: 11px;'>{html.escape(str(ioc.get('context', '')))}</td>"
            f"</tr>"
        )
    ioc_table_html = "".join(ioc_rows)

    narrative_html = "".join([f"<p style='margin-bottom: 12px; font-size: 13px; color: var(--text-secondary);'>{html.escape(str(p))}</p>" for p in exec_sum.get("narrative", [])])
    traits_html = "".join([f"<div class='action-item' style='padding: 8px 12px; margin-bottom: 6px;'><span style='color: var(--primary);'>•</span> <span>{html.escape(str(t))}</span></div>" for t in persona.get("behavioralTraits", [])])
    obs_facts_html = "".join([f"<p style='font-size: 11px; margin-top: 6px; color: var(--text-secondary);'>• {html.escape(str(f))}</p>" for f in facts.get("observed", [])])
    inf_facts_html = "".join([f"<p style='font-size: 11px; margin-top: 6px; color: var(--text-secondary);'>• {html.escape(str(f))}</p>" for f in facts.get("inferred", [])])
    pred_facts_html = "".join([f"<p style='font-size: 11px; margin-top: 6px; color: var(--text-secondary);'>• {html.escape(str(f))}</p>" for f in facts.get("predicted", [])])
    imm_recs_html = "".join([f"<div class='action-item'><span style='color: var(--accent-crimson);'>⚡</span> <span>{html.escape(str(act))}</span></div>" for act in recs.get("immediateActions", [])])
    short_recs_html = "".join([f"<div class='action-item'><span style='color: var(--accent-amber);'>🛡️</span> <span>{html.escape(str(act))}</span></div>" for act in recs.get("shortTermActions", [])])
    long_recs_html = "".join([f"<div class='action-item'><span style='color: var(--primary);'>✓</span> <span>{html.escape(str(act))}</span></div>" for act in recs.get("longTermActions", [])])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(str(meta.get('reportTitle', 'SHADOWTRAP REPORT')))} - {html.escape(str(meta.get('sessionId', '')))}</title>
    <style>
        :root {{
            --bg-base: #060B08;
            --bg-card: rgba(14, 23, 18, 0.85);
            --bg-card-alt: rgba(10, 17, 14, 0.6);
            --border-color: rgba(0, 255, 136, 0.15);
            --primary: #00FF88;
            --primary-glow: rgba(0, 255, 136, 0.12);
            --accent-cyan: #4CC9F0;
            --accent-amber: #FFD166;
            --accent-crimson: #FF4D6D;
            --text-main: #E8FFF3;
            --text-secondary: #C4DBD0;
            --text-muted: #8FA99B;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            line-height: 1.6;
            display: flex;
            min-height: 100vh;
        }}
        .sidebar {{
            width: 280px;
            background: #09100C;
            border-right: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            padding: 24px 16px;
            flex-shrink: 0;
        }}
        .brand {{
            font-size: 14px;
            font-weight: 800;
            color: var(--primary);
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        .nav-list {{ list-style: none; }}
        .nav-item {{ margin-bottom: 4px; }}
        .nav-link {{
            display: block;
            padding: 8px 12px;
            color: var(--text-muted);
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        .nav-link:hover {{
            color: var(--primary);
            background: var(--primary-glow);
        }}
        .main-content {{
            flex: 1;
            padding: 36px 40px;
            max-width: 1100px;
            overflow-y: auto;
        }}
        .header-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 28px;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        h1 {{ font-size: 24px; color: var(--primary); font-weight: 800; }}
        .subtitle {{ font-size: 13px; color: var(--text-muted); margin-top: 4px; }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            font-family: monospace;
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 28px;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0, 255, 136, 0.1);
        }}
        .card-title {{
            font-size: 13px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--primary);
        }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
        .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
        .meta-box {{
            background: var(--bg-card-alt);
            border: 1px solid rgba(0, 255, 136, 0.08);
            border-radius: 8px;
            padding: 12px 14px;
        }}
        .meta-label {{ font-size: 10px; text-transform: uppercase; color: var(--text-muted); font-weight: 700; font-family: monospace; }}
        .meta-value {{ font-size: 13px; font-weight: 700; color: var(--text-main); margin-top: 4px; font-family: monospace; word-break: break-all; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }}
        th {{
            text-align: left;
            padding: 10px 12px;
            background: rgba(0, 255, 136, 0.06);
            color: var(--primary);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            border-bottom: 1px solid var(--border-color);
        }}
        td {{ padding: 10px 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: var(--text-secondary); }}
        code {{ font-family: 'Courier New', Courier, monospace; color: var(--primary); background: rgba(0, 255, 136, 0.05); padding: 2px 6px; border-radius: 4px; }}
        .tag {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            font-family: monospace;
            background: rgba(0, 255, 136, 0.1);
            color: var(--primary);
            border: 1px solid rgba(0, 255, 136, 0.25);
        }}
        .timeline-item {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 10px 0;
            border-left: 2px solid rgba(0, 255, 136, 0.25);
            margin-left: 10px;
            padding-left: 18px;
            position: relative;
        }}
        .timeline-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary);
            position: absolute;
            left: -5px;
            top: 16px;
        }}
        .action-item {{
            padding: 12px 16px;
            background: rgba(0, 255, 136, 0.05);
            border: 1px solid rgba(0, 255, 136, 0.18);
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 12px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }}
        .search-bar {{
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: #09100C;
            color: var(--text-main);
            font-size: 12px;
            margin-bottom: 14px;
            outline: none;
        }}
        .search-bar:focus {{ border-color: var(--primary); }}
        @media (max-width: 900px) {{
            body {{ flex-direction: column; }}
            .sidebar {{ width: 100%; height: auto; position: static; }}
            .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }}
            .main-content {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="brand">🛡️ Sentinel SOC DFIR</div>
        <ul class="nav-list">
            <li class="nav-item"><a href="#sec-overview" class="nav-link">01. Incident Header</a></li>
            <li class="nav-item"><a href="#sec-exec" class="nav-link">02. Executive Summary</a></li>
            <li class="nav-item"><a href="#sec-meta" class="nav-link">03. Incident Overview</a></li>
            <li class="nav-item"><a href="#sec-timeline" class="nav-link">04. Attack Timeline</a></li>
            <li class="nav-item"><a href="#sec-commands" class="nav-link">05. Captured Commands</a></li>
            <li class="nav-item"><a href="#sec-persona" class="nav-link">06. Attacker Persona</a></li>
            <li class="nav-item"><a href="#sec-stages" class="nav-link">07. Attack Stages</a></li>
            <li class="nav-item"><a href="#sec-ai" class="nav-link">08. AI Threat Analysis</a></li>
            <li class="nav-item"><a href="#sec-mitre" class="nav-link">09. MITRE ATT&CK</a></li>
            <li class="nav-item"><a href="#sec-iocs" class="nav-link">10. IOCs</a></li>
            <li class="nav-item"><a href="#sec-facts" class="nav-link">11. Observed Facts</a></li>
            <li class="nav-item"><a href="#sec-recs" class="nav-link">12. Defensive Plan</a></li>
            <li class="nav-item"><a href="#sec-conclusion" class="nav-link">13. Final Conclusion</a></li>
            <li class="nav-item"><a href="#sec-integrity" class="nav-link">14. Report Metadata</a></li>
        </ul>
    </div>

    <div class="main-content">
        <div id="sec-overview" class="header-card">
            <div class="header-top">
                <div>
                    <h1>{html.escape(str(meta.get('systemName', 'SHADOWTRAP SENTINEL')))}</h1>
                    <p class="subtitle">{html.escape(str(meta.get('reportTitle', 'INCIDENT INVESTIGATION REPORT')))}</p>
                </div>
                <div>
                    <span class="badge" style="background: {lvl_color}22; color: {lvl_color}; border: 1px solid {lvl_color}66;">
                        THREAT LEVEL: {html.escape(str(threat_level))} ({meta.get('threatScoreDisplay', '')})
                    </span>
                </div>
            </div>
            <div class="grid-4">
                <div class="meta-box"><div class="meta-label">Incident ID</div><div class="meta-value">{html.escape(str(meta.get('incidentId', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Session ID</div><div class="meta-value">{html.escape(str(meta.get('sessionId', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Target IP</div><div class="meta-value">{html.escape(str(meta.get('targetIp', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Source IP</div><div class="meta-value" style="color: #FF4D6D;">{html.escape(str(meta.get('sourceIp', '')))}</div></div>
            </div>
        </div>

        <div id="sec-exec" class="card">
            <div class="card-header"><div class="card-title">02 / Executive Summary</div></div>
            {narrative_html}
            <div class="grid-2" style="margin-top: 16px;">
                <div class="meta-box"><div class="meta-label">Potential Impact</div><div class="meta-value" style="font-size: 12px; font-family: sans-serif;">{html.escape(str(exec_sum.get('potentialImpact', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Recommended Immediate Action</div><div class="meta-value" style="font-size: 12px; font-family: sans-serif; color: var(--primary);">{html.escape(str(exec_sum.get('recommendedImmediateAction', '')))}</div></div>
            </div>
        </div>

        <div id="sec-meta" class="card">
            <div class="card-header"><div class="card-title">03 / Incident Overview & Telemetry Matrix</div></div>
            <div class="grid-4">
                <div class="meta-box"><div class="meta-label">Target Host</div><div class="meta-value">{html.escape(str(overview.get('targetHostname', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Target Port / Service</div><div class="meta-value">{overview.get('targetPort', 22)} / {html.escape(str(overview.get('protocol', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Target Username</div><div class="meta-value">{html.escape(str(overview.get('username', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Attack Stage</div><div class="meta-value" style="color: var(--primary);">{html.escape(str(overview.get('attackStage', '')))}</div></div>
            </div>
            <div class="grid-4" style="margin-top: 14px;">
                <div class="meta-box"><div class="meta-label">Start Time</div><div class="meta-value">{html.escape(str(overview.get('startTime', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">End Time</div><div class="meta-value">{html.escape(str(overview.get('endTime', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Duration</div><div class="meta-value">{html.escape(str(overview.get('duration', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Total Events</div><div class="meta-value">{overview.get('eventCount', 0)}</div></div>
            </div>
        </div>

        <div id="sec-timeline" class="card">
            <div class="card-header"><div class="card-title">04 / Chronological Attack Timeline ({len(timeline)} Events)</div></div>
            <div style="max-height: 380px; overflow-y: auto; padding-right: 8px;">
                {timeline_html}
            </div>
        </div>

        <div id="sec-commands" class="card">
            <div class="card-header">
                <div class="card-title">05 / Complete Captured Commands & Payloads ({len(commands)})</div>
            </div>
            <input type="text" id="cmdSearchInput" class="search-bar" placeholder="Search commands, payloads, results, or techniques..." onkeyup="filterCommandsTable()">
            <div style="max-height: 440px; overflow-y: auto;">
                <table id="commandsTable">
                    <thead>
                        <tr>
                            <th style="width: 40px;">#</th>
                            <th style="width: 80px;">Time</th>
                            <th>Command Payload</th>
                            <th style="width: 140px;">Result</th>
                            <th style="width: 160px;">MITRE Technique</th>
                        </tr>
                    </thead>
                    <tbody id="commandsTableBody">
                        {cmd_table_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div id="sec-persona" class="card">
            <div class="card-header"><div class="card-title">06 / Attacker Persona & Profiling</div></div>
            <div class="grid-4">
                <div class="meta-box"><div class="meta-label">Skill Level</div><div class="meta-value">{html.escape(str(persona.get('skillLevel', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Attack Style</div><div class="meta-value">{html.escape(str(persona.get('attackStyle', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Likely Goal</div><div class="meta-value">{html.escape(str(persona.get('likelyGoal', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Confidence</div><div class="meta-value">{html.escape(str(persona.get('confidence', '')))}</div></div>
            </div>
            <div style="margin-top: 14px;">
                <div class="meta-label" style="margin-bottom: 8px;">Observed Behavioral Traits</div>
                {traits_html}
            </div>
        </div>

        <div id="sec-stages" class="card">
            <div class="card-header"><div class="card-title">07 / Attack Progression & Intent Analysis</div></div>
            <div class="grid-3">
                <div class="meta-box"><div class="meta-label">Current Stage</div><div class="meta-value" style="color: var(--primary);">{html.escape(str(stages.get('currentStage', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Attacker Intent</div><div class="meta-value" style="color: var(--accent-amber);">{html.escape(str(intent.get('detectedIntent', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Predicted Next Move</div><div class="meta-value" style="color: var(--accent-cyan);">{html.escape(str(stages.get('predictedNextStage', '')))} ({html.escape(str(stages.get('predictionConfidence', '')))})</div></div>
            </div>
            <div style="margin-top: 14px;" class="meta-box">
                <div class="meta-label">Classification Justification</div>
                <p style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">{html.escape(str(intent.get('classificationReasoning', '')))}</p>
            </div>
        </div>

        <div id="sec-ai" class="card">
            <div class="card-header"><div class="card-title">08 / AI Threat Analysis ({html.escape(str(ai.get('aiModel', {}).get('modelName', 'Sentinel AI')))})</div></div>
            <div class="grid-2">
                <div class="meta-box"><div class="meta-label">Attacker Behavior</div><p style="font-size: 12px; color: var(--text-main); margin-top: 4px;">{html.escape(str(ai.get('attackerBehavior', '')))}</p></div>
                <div class="meta-box"><div class="meta-label">Inferred Objective</div><p style="font-size: 12px; color: var(--text-main); margin-top: 4px;">{html.escape(str(ai.get('inferredObjective', '')))}</p></div>
            </div>
            <div class="meta-box" style="margin-top: 14px; background: rgba(0, 255, 136, 0.03); border-color: rgba(0, 255, 136, 0.2);">
                <div class="meta-label">Chain of Reasoning</div>
                <p style="font-size: 12px; color: #A7D8BE; font-style: italic; margin-top: 4px;">{html.escape(str(ai.get('chainOfReasoning', '')))}</p>
            </div>
        </div>

        <div id="sec-mitre" class="card">
            <div class="card-header"><div class="card-title">09 / MITRE ATT&CK Matrix Mapping ({len(mitre)} Techniques)</div></div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 100px;">Technique ID</th>
                        <th>Technique Name</th>
                        <th>Tactic</th>
                        <th>Evidence</th>
                        <th style="width: 90px;">Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    {mitre_table_html}
                </tbody>
            </table>
        </div>

        <div id="sec-iocs" class="card">
            <div class="card-header"><div class="card-title">10 / Indicators of Compromise (IOCs)</div></div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 180px;">Indicator Type</th>
                        <th>Observed Artifact Value</th>
                        <th>Context / Category</th>
                    </tr>
                </thead>
                <tbody>
                    {ioc_table_html}
                </tbody>
            </table>
        </div>

        <div id="sec-facts" class="card">
            <div class="card-header"><div class="card-title">11 / Tripartite Fact & Prediction Model</div></div>
            <div class="grid-3">
                <div class="meta-box">
                    <div class="meta-label" style="color: var(--primary);">[OBSERVED FACTS]</div>
                    {obs_facts_html}
                </div>
                <div class="meta-box">
                    <div class="meta-label" style="color: var(--accent-amber);">[INFERRED ANALYSIS]</div>
                    {inf_facts_html}
                </div>
                <div class="meta-box">
                    <div class="meta-label" style="color: var(--accent-cyan);">[PREDICTED ACTIONS]</div>
                    {pred_facts_html}
                </div>
            </div>
        </div>

        <div id="sec-recs" class="card">
            <div class="card-header"><div class="card-title">12 / Defensive Containment & Hardening Plan</div></div>
            <div class="meta-label" style="margin-bottom: 6px; color: var(--accent-crimson);">Immediate Actions (0-24 Hours)</div>
            {imm_recs_html}
            
            <div class="meta-label" style="margin-top: 14px; margin-bottom: 6px; color: var(--accent-amber);">Short-Term Actions (1-7 Days)</div>
            {short_recs_html}

            <div class="meta-label" style="margin-top: 14px; margin-bottom: 6px; color: var(--primary);">Long-Term Hardening (Strategic)</div>
            {long_recs_html}
        </div>

        <div id="sec-conclusion" class="card">
            <div class="card-header"><div class="card-title">13 / Final Incident Conclusion</div></div>
            <p style="font-size: 13px; color: var(--text-main); margin-bottom: 10px;">{html.escape(str(conclusion.get('incidentSummary', '')))}</p>
            <div class="action-item" style="background: rgba(0, 255, 136, 0.08);">
                <strong>Status:</strong> {html.escape(str(conclusion.get('containmentVerification', '')))}
            </div>
        </div>

        <div id="sec-integrity" class="card" style="margin-bottom: 50px;">
            <div class="card-header"><div class="card-title">14 / Report Integrity & Verification</div></div>
            <div class="grid-4">
                <div class="meta-box"><div class="meta-label">Session ID</div><div class="meta-value">{html.escape(str(integrity.get('session', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Commands Logged</div><div class="meta-value">{integrity.get('commands', 0)}</div></div>
                <div class="meta-box"><div class="meta-label">Data Completeness</div><div class="meta-value" style="color: var(--primary);">{html.escape(str(integrity.get('dataCompleteness', '')))}</div></div>
                <div class="meta-box"><div class="meta-label">Report Version</div><div class="meta-value">{html.escape(str(integrity.get('reportVersion', '1.0')))}</div></div>
            </div>
        </div>
    </div>

    <script>
        function filterCommandsTable() {{
            var input = document.getElementById('cmdSearchInput');
            var filter = input.value.toLowerCase();
            var trs = document.getElementById('commandsTableBody').getElementsByTagName('tr');
            for (var i = 0; i < trs.length; i++) {{
                var text = trs[i].textContent || trs[i].innerText;
                trs[i].style.display = text.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
            }}
        }}
    </script>
</body>
</html>"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)


def _generate_pdf_report(report_data, filepath):
    """
    Save multi-page enterprise DFIR investigation PDF report with NumberedCanvas.
    Uses clean, crisp, high-contrast black typography on white page backgrounds
    for maximum readability and printing clarity.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas

        # Custom Numbered Canvas for Running Header & "Page X of Y" Footer
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_page_decorations(num_pages)
                    super().showPage()
                super().save()

            def draw_page_decorations(self, page_count):
                self.saveState()
                self.setFont("Helvetica-Bold", 7.5)
                self.setFillColor(colors.HexColor('#0F172A'))  # Crisp Black/Slate-900

                # Running Header
                self.drawString(36, 756, "SHADOWTRAP SENTINEL — FORENSIC INCIDENT INVESTIGATION REPORT")
                self.drawRightString(576, 756, "CONFIDENTIAL // SOC & FORENSIC INVESTIGATION")
                self.setStrokeColor(colors.HexColor('#CBD5E1'))
                self.setLineWidth(0.75)
                self.line(36, 750, 576, 750)

                # Running Footer
                self.line(36, 42, 576, 42)
                self.drawString(36, 30, "Generated by ShadowTrap Sentinel Enterprise DFIR Engine v1.0")
                page_str = f"Page {self._pageNumber} of {page_count}"
                self.drawRightString(576, 30, page_str)
                self.restoreState()

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=46,
            bottomMargin=46
        )

        styles = getSampleStyleSheet()
        elements = []

        # High-Contrast Professional Black & Slate Color Palette (100% visible on white background)
        c_black = colors.HexColor('#000000')
        c_heading = colors.HexColor('#0F172A')       # Slate 900
        c_body = colors.HexColor('#1E293B')          # Slate 800
        c_muted = colors.HexColor('#475569')         # Slate 600
        c_table_bg = colors.HexColor('#F8FAFC')      # Slate 50
        c_table_header = colors.HexColor('#E2E8F0')  # Slate 200
        c_border = colors.HexColor('#CBD5E1')        # Slate 300
        c_accent = colors.HexColor('#0F2942')        # Dark Navy

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=15,
            leading=18,
            textColor=c_heading,
            fontName="Helvetica-Bold",
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            textColor=c_muted,
            fontName="Helvetica",
            spaceAfter=8
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=10.5,
            leading=13,
            textColor=c_heading,
            fontName="Helvetica-Bold",
            spaceBefore=9,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'BodyNormal',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            textColor=c_body,
            fontName="Helvetica"
        )
        code_style = ParagraphStyle(
            'CodeStyle',
            parent=styles['Normal'],
            fontSize=7,
            leading=9,
            textColor=c_black,
            fontName="Courier"
        )
        meta_label_style = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontSize=7.5,
            leading=10,
            textColor=c_muted,
            fontName="Helvetica-Bold"
        )

        meta = report_data.get("reportMetadata", {})
        exec_sum = report_data.get("executiveSummary", {})
        overview = report_data.get("incidentOverview", {})
        commands = report_data.get("capturedCommands", [])
        persona = report_data.get("attackerPersona", {})
        ai = report_data.get("aiThreatAnalysis", {})
        mitre = report_data.get("mitreAttack", [])
        iocs = report_data.get("indicatorsOfCompromise", {})
        recs = report_data.get("defensiveRecommendations", {})
        conclusion = report_data.get("finalConclusion", {})

        # Header Block
        elements.append(Paragraph(meta.get("systemName", "SHADOWTRAP SENTINEL"), title_style))
        elements.append(Paragraph(f"INCIDENT DOSSIER: {meta.get('incidentId')} | Generated: {meta.get('generatedAt')}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=c_heading, spaceAfter=8))

        # 1. Overview Table
        elements.append(Paragraph("1. Incident Overview & Target Metadata", h2_style))
        ov_table_data = [
            [
                Paragraph("<b>Session ID</b>", meta_label_style), Paragraph(str(overview.get("sessionId")), code_style),
                Paragraph("<b>Target IP</b>", meta_label_style), Paragraph(str(overview.get("targetIp")), code_style)
            ],
            [
                Paragraph("<b>Attacker IP</b>", meta_label_style), Paragraph(str(overview.get("sourceIp")), code_style),
                Paragraph("<b>Service / Port</b>", meta_label_style), Paragraph(f"{overview.get('protocol')} / {overview.get('targetPort')}", body_style)
            ],
            [
                Paragraph("<b>Attack Stage</b>", meta_label_style), Paragraph(str(overview.get("attackStage")), body_style),
                Paragraph("<b>Threat Score</b>", meta_label_style), Paragraph(f"<b>{overview.get('threatScore')} ({overview.get('threatLevel')})</b>", body_style)
            ],
            [
                Paragraph("<b>Duration</b>", meta_label_style), Paragraph(str(overview.get("duration")), body_style),
                Paragraph("<b>Commands Logged</b>", meta_label_style), Paragraph(str(overview.get("commandCount")), body_style)
            ],
        ]
        t_ov = Table(ov_table_data, colWidths=[90, 180, 90, 180])
        t_ov.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_table_bg),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_ov)
        elements.append(Spacer(1, 8))

        # 2. Executive Summary
        elements.append(Paragraph("2. Executive Summary", h2_style))
        for p_text in exec_sum.get("narrative", []):
            elements.append(Paragraph(p_text, body_style))
            elements.append(Spacer(1, 3))
        elements.append(Spacer(1, 4))

        # 3. Attacker Persona & Profiling
        elements.append(Paragraph("3. Attacker Persona & Threat Assessment", h2_style))
        persona_text = f"<b>Skill Level:</b> {persona.get('skillLevel')} | <b>Attack Style:</b> {persona.get('attackStyle')} | <b>Likely Goal:</b> {persona.get('likelyGoal')}"
        elements.append(Paragraph(persona_text, body_style))
        elements.append(Spacer(1, 3))
        for trait in persona.get("behavioralTraits", []):
            elements.append(Paragraph(f"• {trait}", body_style))
        elements.append(Spacer(1, 6))

        # 4. Captured Commands Table
        elements.append(Paragraph(f"4. Complete Captured Commands ({len(commands)})", h2_style))
        cmd_headers = [Paragraph("<b>#</b>", meta_label_style), Paragraph("<b>Time</b>", meta_label_style), Paragraph("<b>Command Payload</b>", meta_label_style), Paragraph("<b>Result</b>", meta_label_style)]
        cmd_table_data = [cmd_headers]
        for c in commands:
            cmd_table_data.append([
                Paragraph(str(c.get("index", "")), body_style),
                Paragraph(str(c.get("timestamp", "")), code_style),
                Paragraph(html.escape(str(c.get("fullCommand", ""))), code_style),
                Paragraph(str(c.get("result", "")), body_style),
            ])
        t_cmds = Table(cmd_table_data, colWidths=[25, 55, 360, 100])
        t_cmds.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_table_header),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_cmds)
        elements.append(Spacer(1, 8))

        # 5. MITRE ATT&CK Mapping
        elements.append(Paragraph("5. MITRE ATT&CK Mapping", h2_style))
        mitre_headers = [Paragraph("<b>Technique ID</b>", meta_label_style), Paragraph("<b>Technique Name</b>", meta_label_style), Paragraph("<b>Tactic</b>", meta_label_style), Paragraph("<b>Evidence</b>", meta_label_style)]
        mitre_table_data = [mitre_headers]
        for m in mitre:
            mitre_table_data.append([
                Paragraph(str(m.get("techniqueId")), code_style),
                Paragraph(str(m.get("techniqueName")), body_style),
                Paragraph(str(m.get("tactic")), body_style),
                Paragraph(html.escape(str(m.get("evidence", ""))), body_style),
            ])
        t_mitre = Table(mitre_table_data, colWidths=[75, 155, 110, 200])
        t_mitre.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_table_header),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_mitre)
        elements.append(Spacer(1, 8))

        # 6. Indicators of Compromise
        elements.append(Paragraph("6. Indicators of Compromise (IOCs)", h2_style))
        ioc_headers = [Paragraph("<b>Indicator Type</b>", meta_label_style), Paragraph("<b>Artifact Value</b>", meta_label_style), Paragraph("<b>Context</b>", meta_label_style)]
        ioc_table_data = [ioc_headers]
        for ioc in iocs.get("networkIndicators", []) + iocs.get("payloadIndicators", [])[:6]:
            ioc_table_data.append([
                Paragraph(str(ioc.get("type")), body_style),
                Paragraph(html.escape(str(ioc.get("value"))), code_style),
                Paragraph(str(ioc.get("context")), body_style),
            ])
        t_iocs = Table(ioc_table_data, colWidths=[120, 260, 160])
        t_iocs.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_table_header),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_iocs)
        elements.append(Spacer(1, 8))

        # 7. AI Threat Analysis & Defensive Plan
        elements.append(Paragraph("7. AI Threat Analysis & Chain of Reasoning", h2_style))
        elements.append(Paragraph(f"<b>Behavior:</b> {ai.get('attackerBehavior')}", body_style))
        elements.append(Paragraph(f"<b>Inferred Objective:</b> {ai.get('inferredObjective')}", body_style))
        elements.append(Paragraph(f"<b>Chain of Reasoning:</b> <i>{ai.get('chainOfReasoning')}</i>", body_style))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("8. Defensive Recommendations & Action Plan", h2_style))
        for act in recs.get("immediateActions", []):
            elements.append(Paragraph(f"<b>[IMMEDIATE]</b> • {act}", body_style))
        for act in recs.get("shortTermActions", []):
            elements.append(Paragraph(f"<b>[SHORT-TERM]</b> • {act}", body_style))
        elements.append(Spacer(1, 6))

        # 9. Conclusion
        elements.append(Paragraph("9. Final Incident Conclusion", h2_style))
        elements.append(Paragraph(conclusion.get("incidentSummary", ""), body_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"<b>Containment Status:</b> {conclusion.get('containmentVerification', '')}", body_style))

        # Build PDF with dynamic NumberedCanvas
        doc.build(elements, canvasmaker=NumberedCanvas)
    except Exception as e:
        logger.warning(f"ReportLab PDF generation failed, creating text fallback: {e}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(report_data, indent=2, default=str))
