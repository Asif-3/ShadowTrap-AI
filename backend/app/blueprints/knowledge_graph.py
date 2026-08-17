"""
ShadowTrap AI X — Knowledge Graph Blueprint
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.knowledge_graph_service import build_knowledge_graph
from app.utils.decorators import handle_errors

knowledge_graph_bp = Blueprint("knowledge_graph", __name__, url_prefix="/api/knowledge-graph")


@knowledge_graph_bp.route("", methods=["GET"])
@handle_errors
@jwt_required()
def get_graph():
    session_ids = request.args.getlist("session_id")
    graph_data = build_knowledge_graph(session_ids if session_ids else None)
    return jsonify({"success": True, "data": graph_data}), 200


@knowledge_graph_bp.route("/session/<session_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_session_graph(session_id):
    graph_data = build_knowledge_graph([session_id])
    return jsonify({"success": True, "data": graph_data}), 200
