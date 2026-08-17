"""
ShadowTrap AI - Reports Blueprint
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.report import get_reports, get_report_by_id, delete_report
from app.services.report_service import generate_report
from app.utils.decorators import handle_errors, validate_json

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.route("", methods=["GET"])
@handle_errors
@jwt_required()
def list_reports():
    """Get paginated list of reports."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return jsonify({"success": True, "data": get_reports(page, per_page)}), 200


@reports_bp.route("/generate", methods=["POST"])
@handle_errors
@jwt_required()
@validate_json("session_id")
def create_report():
    """Generate a new report."""
    data = request.get_json()
    user_id = get_jwt_identity()
    fmt = data.get("format", "pdf")
    send_telegram = data.get("send_telegram", False)
    
    report = generate_report(data["session_id"], fmt, user_id)
    
    if send_telegram:
        try:
            from app.services.telegram_service import send_report_document
            send_report_document(report)
        except Exception as e:
            pass
            
    return jsonify({"success": True, "data": report, "message": f"Report generated ({fmt})"}), 201


@reports_bp.route("/<report_id>", methods=["GET"])
@handle_errors
@jwt_required()
def get_report(report_id):
    """Get report details."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404
    return jsonify({"success": True, "data": report}), 200


@reports_bp.route("/<report_id>/download", methods=["GET"])
@reports_bp.route("/download/<report_id>", methods=["GET"])
@handle_errors
@jwt_required()
def download_report(report_id):
    """Download a report file."""
    import os
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404
    
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path = report.get("file_path", "") or report.get("filepath", "")
    
    if file_path and not os.path.isabs(file_path):
        file_path = os.path.abspath(os.path.join(backend_dir, file_path))

    # Check fallback in reports directory if recorded path does not exist
    if not file_path or not os.path.exists(file_path):
        filename = report.get("filename", "")
        if filename:
            fallback_path = os.path.abspath(os.path.join(backend_dir, "reports", filename))
            if os.path.exists(fallback_path):
                file_path = fallback_path

    # Auto-regenerate report on the fly if file is missing
    if not file_path or not os.path.exists(file_path):
        session_id = report.get("session_id")
        fmt = report.get("format", "pdf")
        if session_id:
            try:
                regen_report = generate_report(session_id, fmt)
                file_path = regen_report.get("file_path")
            except Exception as e:
                return jsonify({"success": False, "error": f"Report file not found and regeneration failed: {str(e)}"}), 404

    if not file_path or not os.path.exists(file_path):
        return jsonify({"success": False, "error": "Report file not found on disk"}), 404
    
    # Record download event in database
    from app.models.report import record_report_download
    record_report_download(report.get("_id", report_id))

    mime_types = {"pdf": "application/pdf", "html": "text/html", "json": "application/json"}
    filename = report.get("filename", os.path.basename(file_path))
    fmt = report.get("format", "pdf")
    return send_file(
        file_path,
        mimetype=mime_types.get(fmt, "application/octet-stream"),
        as_attachment=True,
        download_name=filename
    )


@reports_bp.route("/<report_id>/send-telegram", methods=["POST"])
@reports_bp.route("/send-telegram/<report_id>", methods=["POST"])
@handle_errors
@jwt_required()
def send_report_telegram(report_id):
    """Send a report document directly to Telegram."""
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404
        
    from app.services.telegram_service import send_report_document
    sent = send_report_document(report)
    if not sent:
        return jsonify({"success": False, "error": "Failed to send report to Telegram. Check bot configuration and chat registration."}), 400
        
    return jsonify({"success": True, "message": f"Report '{report.get('filename')}' sent to Telegram successfully."}), 200


@reports_bp.route("/<report_id>", methods=["DELETE"])
@handle_errors
@jwt_required()
def remove_report(report_id):
    """Delete a report."""
    deleted = delete_report(report_id)
    if not deleted:
        return jsonify({"success": False, "error": "Report not found"}), 404
    return jsonify({"success": True, "message": "Report deleted"}), 200

