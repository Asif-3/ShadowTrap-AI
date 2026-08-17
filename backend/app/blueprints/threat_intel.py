"""
ShadowTrap AI — Threat Intelligence Blueprint
=================================================
Provides endpoints for Global Threat Intelligence:
- Summary metrics
- Honeypot IP Reputation Feed
- Per-IP Attack Activity summary
- Chronological Recent Attacks list
- IP Details Modal lookup
- Aggregated Attack Statistics (Country, Region, City, IP, Protocol, Time)
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import get_db
from app.utils.decorators import handle_errors
from app.utils.helpers import serialize_doc, serialize_docs, utc_now
from app.services.ip_intel_service import lookup_ip

threat_intel_bp = Blueprint("threat_intel", __name__, url_prefix="/api/threat-intel")


@threat_intel_bp.route("/overview", methods=["GET"])
@threat_intel_bp.route("/full", methods=["GET"])
@handle_errors
@jwt_required()
def get_full_threat_intel():
    """Get complete Global Threat Intelligence dataset."""
    db = get_db()
    
    # 1. Total attacks & distinct IPs
    total_attacks = db.attacks.count_documents({})
    unique_ips = db.attacks.distinct("src_ip")
    
    # Enrich all unique IPs with IP-API lookup (cached)
    ip_intel_map = {}
    for ip in unique_ips:
        if ip:
            intel = lookup_ip(ip)
            ip_intel_map[ip] = intel

    # Distinct geolocation counters
    countries = set()
    cities = set()
    regions = set()
    high_threat_ips = set()
    c2_servers = set()
    live_active = 0

    for ip, intel in ip_intel_map.items():
        if intel.get("country") and intel["country"] != "Unknown":
            countries.add(intel["country"])
        if intel.get("city") and intel["city"] != "Unknown":
            cities.add(intel["city"])
        if intel.get("regionName") and intel["regionName"] != "Unknown":
            regions.add(intel["regionName"])
        elif intel.get("region") and intel["region"] != "Unknown":
            regions.add(intel["region"])

        if intel.get("proxy") or intel.get("hosting"):
            c2_servers.add(ip)

    # 2. Per-IP Aggregation for Reputation Table & Attack Activity
    reputation_feed = []
    ip_activity = []

    for ip in unique_ips:
        if not ip:
            continue
            
        sessions = list(db.attacks.find({"src_ip": ip}).sort("created_at", 1))
        if not sessions:
            continue

        atk_count = len(sessions)
        latest_atk = sessions[-1]
        first_atk = sessions[0]

        max_threat_score = max(s.get("threat_score", 0) for s in sessions)
        if max_threat_score >= 60:
            high_threat_ips.add(ip)

        intent = latest_atk.get("intent", "")
        if any(c2_term in str(intent).lower() for c2_term in ["command", "c2", "exfiltration", "control"]):
            c2_servers.add(ip)

        is_live = any(s.get("is_live", False) for s in sessions)
        if is_live:
            live_active += 1

        intel = ip_intel_map.get(ip, {})

        # Collect command stats
        all_commands = []
        download_count = 0
        login_attempts = 0
        successful_logins = 0

        for s in sessions:
            cmds = s.get("commands", [])
            all_commands.extend(cmds)
            for c in cmds:
                c_lower = str(c).lower()
                if any(dl in c_lower for dl in ["wget", "curl", "tftp", "chmod", "base64", "./"]):
                    download_count += 1
                if "hydra" in c_lower or "login" in c_lower or "pass=" in c_lower or "user=" in c_lower:
                    login_attempts += 1
                    if "cracked" in c_lower or "granted" in c_lower or "success" in c_lower:
                        successful_logins += 1

        protocol = latest_atk.get("protocol", "SSH").upper()
        if not protocol:
            protocol = "SSH"

        status_str = "Live" if is_live else ("High Threat" if max_threat_score >= 60 else "Monitored")

        intel_country = intel.get("country", "Local/Private Network" if ip in ["127.0.0.1", "localhost"] else "Unknown")
        intel_region = intel.get("regionName", intel.get("region", "Local Network"))
        intel_city = intel.get("city", "Local Network")
        intel_isp = intel.get("isp", intel.get("org", "Private Network"))
        intel_asn = intel.get("asn", intel.get("as", ""))

        reputation_feed.append({
            "ip": ip,
            "country": intel_country,
            "country_code": intel.get("countryCode", "LOCAL" if "127.0.0.1" in ip else "XX"),
            "region": intel_region,
            "city": intel_city,
            "isp": intel_isp,
            "asn": intel_asn,
            "attack_count": atk_count,
            "threat_score": max_threat_score,
            "status": status_str,
            "last_seen": latest_atk.get("created_at"),
        })

        ip_activity.append({
            "ip": ip,
            "total_attacks": atk_count,
            "first_seen": first_atk.get("created_at"),
            "last_seen": latest_atk.get("created_at"),
            "protocol": protocol,
            "login_attempts": max(login_attempts, atk_count),
            "successful_logins": successful_logins,
            "commands_executed": len(all_commands),
            "download_attempts": download_count,
            "attack_type": latest_atk.get("attack_stage", "Discovery"),
            "threat_score": max_threat_score,
            "status": "Live" if is_live else "Inactive",
        })

    # Sort feeds by threat score & last seen
    reputation_feed.sort(key=lambda x: (x["threat_score"], x["attack_count"]), reverse=True)
    ip_activity.sort(key=lambda x: x["last_seen"] or "", reverse=True)

    # 3. Recent Attacks list (chronological, newest first)
    recent_docs = list(db.attacks.find().sort("created_at", -1).limit(20))
    recent_attacks = []
    for atk in recent_docs:
        ip = atk.get("src_ip", "127.0.0.1")
        intel = ip_intel_map.get(ip, lookup_ip(ip))
        
        cmds = atk.get("commands", [])
        first_cmd = cmds[0] if cmds else "Session Initialized"

        # Extract username if available
        username = "admin"
        if "user='" in first_cmd:
            try:
                username = first_cmd.split("user='")[1].split("'")[0]
            except Exception:
                pass

        recent_attacks.append({
            "session_id": atk.get("session_id"),
            "timestamp": atk.get("created_at"),
            "ip": ip,
            "country": intel.get("country", "Local/Private Network"),
            "region": intel.get("regionName", intel.get("region", "Local Network")),
            "city": intel.get("city", "Local Network"),
            "attack_type": atk.get("attack_stage", "Discovery"),
            "protocol": atk.get("protocol", "SSH").upper(),
            "username": username,
            "command": first_cmd[:65] + "..." if len(first_cmd) > 65 else first_cmd,
            "threat_score": atk.get("threat_score", 0),
        })

    # 4. Attack Statistics Aggregations
    # By Country
    country_counts = {}
    region_counts = {}
    city_counts = {}
    ip_counts = {}
    protocol_counts = {}

    for item in reputation_feed:
        c = item["country"]
        r = item["region"]
        ci = item["city"]
        ip = item["ip"]
        cnt = item["attack_count"]

        country_counts[c] = country_counts.get(c, 0) + cnt
        region_counts[r] = region_counts.get(r, 0) + cnt
        city_counts[ci] = city_counts.get(ci, 0) + cnt
        ip_counts[ip] = cnt

    for act in ip_activity:
        p = act["protocol"]
        protocol_counts[p] = protocol_counts.get(p, 0) + act["total_attacks"]

    def to_sorted_list(d, key_name="name", limit=10):
        return sorted([{"name": k, key_name: k, "count": v} for k, v in d.items()], key=lambda x: x["count"], reverse=True)[:limit]

    # Time trend (timeline by date)
    timeline_pipeline = [
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    timeline_data = list(db.attacks.aggregate(timeline_pipeline))
    by_time = [{"date": t["_id"], "count": t["count"]} for t in timeline_data if t.get("_id")]

    # 5. Build full response payload
    summary = {
        "total_attacks": total_attacks,
        "unique_attacker_ips": len(unique_ips),
        "high_threat_ips": len(high_threat_ips),
        "tracked_c2_servers": len(c2_servers),
        "total_countries": max(len(countries), 1 if total_attacks > 0 else 0),
        "total_cities": max(len(cities), 1 if total_attacks > 0 else 0),
        "total_regions": max(len(regions), 1 if total_attacks > 0 else 0),
        "active_attackers": max(live_active, len(unique_ips)),
    }

    statistics = {
        "by_country": to_sorted_list(country_counts, "country"),
        "by_region": to_sorted_list(region_counts, "region"),
        "by_city": to_sorted_list(city_counts, "city"),
        "by_ip": to_sorted_list(ip_counts, "ip"),
        "by_protocol": to_sorted_list(protocol_counts, "protocol"),
        "by_time": by_time,
    }

    return jsonify({
        "success": True,
        "data": {
            "summary": summary,
            "reputation_feed": reputation_feed,
            "ip_activity": ip_activity,
            "recent_attacks": recent_attacks,
            "statistics": statistics,
        }
    }), 200


@threat_intel_bp.route("/feed", methods=["GET"])
@handle_errors
@jwt_required()
def get_threat_feed():
    """Returns feed format for reputation components."""
    res = get_full_threat_intel()
    json_data = res.get_json()
    if json_data and json_data.get("success"):
        return jsonify({"success": True, "data": json_data["data"]["reputation_feed"]}), 200
    return res


@threat_intel_bp.route("/landscape", methods=["GET"])
@handle_errors
@jwt_required()
def get_landscape():
    """Returns summary metrics."""
    res = get_full_threat_intel()
    json_data = res.get_json()
    if json_data and json_data.get("success"):
        return jsonify({"success": True, "data": json_data["data"]["summary"]}), 200
    return res


@threat_intel_bp.route("/ip/<ip_address>", methods=["GET"])
@handle_errors
@jwt_required()
def get_ip_details(ip_address):
    """Get complete IP intelligence details and attack history for a specific IP."""
    db = get_db()
    intel = lookup_ip(ip_address)
    
    sessions = list(db.attacks.find({"src_ip": ip_address}).sort("created_at", -1))
    
    all_commands = []
    for s in sessions:
        all_commands.extend(s.get("commands", []))

    first_seen = sessions[-1].get("created_at") if sessions else None
    last_seen = sessions[0].get("created_at") if sessions else None
    max_score = max((s.get("threat_score", 0) for s in sessions), default=0)

    details = {
        "ip": ip_address,
        "country": intel.get("country", "Local/Private Network"),
        "country_code": intel.get("countryCode", "LOCAL" if "127.0.0.1" in ip_address else "XX"),
        "region": intel.get("regionName", intel.get("region", "Local Network")),
        "city": intel.get("city", "Local Network"),
        "lat": intel.get("lat", 0.0),
        "lon": intel.get("lon", 0.0),
        "timezone": intel.get("timezone", "UTC"),
        "isp": intel.get("isp", "Private Network"),
        "org": intel.get("org", "Private Network"),
        "asn": intel.get("asn", intel.get("as", "")),
        "proxy": bool(intel.get("proxy", False)),
        "hosting": bool(intel.get("hosting", False)),
        "total_attacks": len(sessions),
        "first_seen": first_seen,
        "last_seen": last_seen,
        "threat_score": max_score,
        "commands_executed": all_commands,
        "sessions": serialize_docs(sessions),
    }

    return jsonify({"success": True, "data": details}), 200
