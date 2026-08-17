"""
ShadowTrap AI — IP Intelligence Service
==========================================
Enriches public attacker IPs using ip-api.com JSON endpoint:
http://ip-api.com/json/{IP}?fields=status,message,query,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,proxy,hosting

Caches all IP lookups in MongoDB (ip_intelligence) to prevent repetitive API calls.
Identifies and tags private/local IP addresses without making external HTTP queries.
"""

import subprocess
import json
import platform
import urllib.request
import urllib.error
from app.extensions import get_db
from app.utils.helpers import serialize_doc, utc_now
from app.utils.logger import get_logger

logger = get_logger("services.ip_intel")


def is_private_ip(ip):
    """
    Check if IP address is in a private, loopback, or reserved range.
    
    Skips:
    - 127.0.0.1 / localhost / 0.0.0.0 / ::1
    - 10.x.x.x
    - 172.16.x.x – 172.31.x.x
    - 192.168.x.x
    """
    if not ip or ip in ["127.0.0.1", "localhost", "0.0.0.0", "::1"]:
        return True
    
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        f, s = int(parts[0]), int(parts[1])
        if f == 10:
            return True
        if f == 172 and 16 <= s <= 31:
            return True
        if f == 192 and s == 168:
            return True
        if f == 127 or f == 0:
            return True
    except ValueError:
        pass
    return False


def get_private_intel(ip_address):
    """Return structured intel for private/local IP addresses."""
    return {
        "ip": ip_address,
        "query": ip_address,
        "status": "success",
        "country": "Local/Private Network",
        "countryCode": "LOCAL",
        "regionName": "Local Network",
        "region": "Local Network",
        "city": "Local Network",
        "lat": 0.0,
        "lon": 0.0,
        "timezone": "UTC",
        "isp": "Private Network",
        "org": "Private Network",
        "as": "LOCAL",
        "proxy": False,
        "hosting": False,
        "fetched_at": utc_now(),
    }


def lookup_ip(ip_address):
    """
    Look up IP intelligence via ip-api.com with 24-hour MongoDB caching.
    
    API URL: http://ip-api.com/json/{ip_address}?fields=status,message,query,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,proxy,hosting
    
    Args:
        ip_address: IPv4 address string
        
    Returns:
        dict: Geolocation and ISP intelligence
    """
    if not ip_address:
        return get_private_intel("127.0.0.1")
        
    # Check for private IP
    if is_private_ip(ip_address):
        return get_private_intel(ip_address)

    db = get_db()
    
    # 1. Check MongoDB cache first
    cached = db.ip_intelligence.find_one({"ip": ip_address})
    if cached and cached.get("fetched_at"):
        from app.utils.helpers import make_utc_aware
        fetched_dt = make_utc_aware(cached["fetched_at"])
        # If cache is valid (less than 24 hours old), return cached document
        if (utc_now() - fetched_dt).total_seconds() < 86400:
            logger.debug(f"IP intel cache hit: {ip_address}")
            return serialize_doc(cached)

    # 2. Call ip-api.com
    fields = "status,message,query,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,proxy,hosting"
    api_url = f"http://ip-api.com/json/{ip_address}?fields={fields}"
    logger.info(f"Executing IP-API lookup: {api_url}")

    data = None
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "ShadowTrap-AI-SOC/2.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                data = json.loads(body)
    except Exception as e:
        logger.warning(f"urllib failed for {ip_address}: {e}. Trying curl fallback.")
        try:
            cmd = ["curl.exe", "-s", api_url] if platform.system().lower() == "windows" else ["curl", "-s", api_url]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
        except Exception as curl_err:
            logger.error(f"curl fallback error for {ip_address}: {curl_err}")

    # Fallback if API lookup fails
    if not data or data.get("status") != "success":
        msg = data.get("message", "API lookup failed") if isinstance(data, dict) else "Network error"
        logger.error(f"IP-API lookup failed for {ip_address}: {msg}")
        return {
            "ip": ip_address,
            "query": ip_address,
            "status": "fail",
            "country": "Unknown",
            "countryCode": "XX",
            "regionName": "Unknown",
            "city": "Unknown",
            "lat": 0.0,
            "lon": 0.0,
            "timezone": "UTC",
            "isp": "Unknown ISP",
            "org": "Unknown Org",
            "as": "Unknown",
            "proxy": False,
            "hosting": False,
            "fetched_at": utc_now(),
        }

    # 3. Structure intelligence record
    intel = {
        "ip": ip_address,
        "query": data.get("query", ip_address),
        "status": "success",
        "country": data.get("country", "Unknown"),
        "countryCode": data.get("countryCode", "XX"),
        "regionName": data.get("regionName", "Unknown"),
        "region": data.get("regionName", "Unknown"),
        "city": data.get("city", "Unknown"),
        "lat": float(data.get("lat", 0.0)),
        "lon": float(data.get("lon", 0.0)),
        "location": {
            "lat": float(data.get("lat", 0.0)),
            "lng": float(data.get("lon", 0.0)),
        },
        "timezone": data.get("timezone", "UTC"),
        "isp": data.get("isp", "Unknown ISP"),
        "org": data.get("org", "Unknown Org"),
        "as": data.get("as", ""),
        "asn": data.get("as", "").split(" ")[0] if data.get("as") else "",
        "proxy": bool(data.get("proxy", False)),
        "hosting": bool(data.get("hosting", False)),
        "fetched_at": utc_now(),
    }

    # 4. Save to MongoDB cache
    db.ip_intelligence.update_one(
        {"ip": ip_address},
        {"$set": intel},
        upsert=True
    )

    logger.info(f"IP intel stored: {ip_address} → {intel['country']} / {intel['city']}")
    return serialize_doc(intel)


def get_top_countries(limit=10):
    """Get top countries by attack count from IP intelligence cache."""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"country": "$_id", "count": 1, "_id": 0}},
    ]
    return list(db.ip_intelligence.aggregate(pipeline))


def get_top_isps(limit=10):
    """Get top ISPs by attack count from IP intelligence cache."""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$isp", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"isp": "$_id", "count": 1, "_id": 0}},
    ]
    return list(db.ip_intelligence.aggregate(pipeline))
