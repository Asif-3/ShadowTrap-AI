"""
ShadowTrap AI X — AI Models Blueprint
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import handle_errors
from app.ai.self_learning import run_training_pipeline, get_learning_history, get_latest_model_version

ai_models_bp = Blueprint("ai_models", __name__, url_prefix="/api/ai-models")


@ai_models_bp.route("/status", methods=["GET"])
@handle_errors
@jwt_required()
def get_model_status():
    latest = get_latest_model_version()
    return jsonify({"success": True, "data": latest}), 200


@ai_models_bp.route("/history", methods=["GET"])
@handle_errors
@jwt_required()
def get_model_history():
    history = get_learning_history()
    return jsonify({"success": True, "data": history}), 200


@ai_models_bp.route("/retrain", methods=["POST"])
@handle_errors
@jwt_required()
def retrain_models():
    res = run_training_pipeline()
    return jsonify({"success": True, "data": res}), 200
