"""
ShadowTrap AI X — Knowledge Graph Service
============================================
Builds and manages a cybersecurity knowledge graph connecting:
    Attackers ↔ IPs ↔ Commands ↔ Sessions ↔ MITRE Techniques ↔ Files ↔ Malware ↔ Countries

Uses NetworkX for graph topological queries and formats graph data for React Flow visualization.
"""

from app.extensions import get_db
from app.utils.logger import get_logger

logger = get_logger("services.knowledge_graph")


def build_knowledge_graph(session_ids=None):
    """
    Build graph topology connecting all entities in the database or for specific sessions.

    Returns:
        dict: {
            "nodes": list of {id, label, type, data, style},
            "edges": list of {id, source, target, label, animated}
        }
    """
    db = get_db()
    query = {"session_id": {"$in": session_ids}} if session_ids else {}

    attacks = list(db.attacks.find(query).limit(100))

    nodes = {}
    edges = []
    edge_set = set()

    def add_node(node_id, label, node_type, details=None):
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "data": details or {}
            }

    def add_edge(source, target, label="CONNECTED_TO"):
        edge_id = f"e_{source}_{target}"
        if edge_id not in edge_set:
            edge_set.add(edge_id)
            edges.append({
                "id": edge_id,
                "source": source,
                "target": target,
                "label": label,
                "animated": label in ["EXACTED", "DOWNLOADED", "EXECUTED"]
            })

    for atk in attacks:
        sid = atk.get("session_id", "")
        ip = atk.get("src_ip", "0.0.0.0")
        stage = atk.get("attack_stage", "Unknown")
        intent = atk.get("intent", "Unknown")
        score = atk.get("threat_score", 0)

        # Nodes
        session_node_id = f"session_{sid}"
        ip_node_id = f"ip_{ip}"
        stage_node_id = f"stage_{stage}"

        add_node(session_node_id, f"Session {sid[:8]}", "session", {"threat_score": score, "status": atk.get("status")})
        add_node(ip_node_id, ip, "ip", {"ip": ip})
        add_node(stage_node_id, stage, "stage", {"stage": stage})

        # Edges
        add_edge(ip_node_id, session_node_id, "LAUNCHED")
        add_edge(session_node_id, stage_node_id, "REACHED")

        # Commands
        for cmd in atk.get("commands", [])[:5]:
            cmd_hash = str(abs(hash(cmd)))[:8]
            cmd_node_id = f"cmd_{cmd_hash}"
            add_node(cmd_node_id, cmd[:20] + "..." if len(cmd) > 20 else cmd, "command", {"command": cmd})
            add_edge(session_node_id, cmd_node_id, "EXECUTED")

        # Downloaded Files
        for f in atk.get("downloaded_files", []):
            fname = f.get("outfile") or f.get("url", "").split("/")[-1] or "payload"
            file_node_id = f"file_{abs(hash(fname))}"
            add_node(file_node_id, fname, "file", {"url": f.get("url")})
            add_edge(session_node_id, file_node_id, "DOWNLOADED")

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
    }
