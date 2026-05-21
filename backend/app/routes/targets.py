"""
Vigil — Target Routes
=====================
/api/targets CRUD, per-target logs, and per-target manual ping.
"""

from flask import Blueprint, request, jsonify, g

from app import db
from app.models import Target, Log
from app.utils import check_url, token_required, create_log_from_result

targets_bp = Blueprint("targets", __name__)


@targets_bp.route("/api/targets", methods=["GET"])
@token_required
def get_targets():
    targets = Target.query.filter_by(user_id=g.current_user.id).order_by(Target.id.desc()).all()
    result = []

    for t in targets:
        logs = Log.query.filter_by(target_id=t.id).order_by(Log.timestamp.desc()).all()

        current_status = "Unknown"
        stats = None

        if logs:
            current_status = logs[0].status
            total_checks = len(logs)
            up_logs = [l for l in logs if l.status == "Up"]
            up_checks = len(up_logs)
            down_checks = total_checks - up_checks
            availability = round((up_checks / total_checks) * 100, 2) if total_checks > 0 else 0

            valid_response_times = [l.response_time for l in up_logs if l.response_time > 0]
            avg_latency = round(sum(valid_response_times) / len(valid_response_times), 2) if valid_response_times else 0

            stats = {
                "totalChecks": total_checks,
                "upChecks": up_checks,
                "downChecks": down_checks,
                "availability": f"{availability}%",
                "averageLatency": f"{avg_latency}"
            }

        result.append({
            "id": t.id,
            "name": t.name,
            "url": t.url,
            "status": current_status,
            "user_id": t.user_id,
            "stats": stats,
            "last_checked": logs[0].timestamp.isoformat() if logs else None,
        })

    return jsonify({"count": len(result), "targets": result}), 200


@targets_bp.route("/api/targets", methods=["POST"])
@token_required
def add_target():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    url  = data.get("url", "").strip()

    if not name or not url:
        return jsonify({"status": "fail", "message": "name and url are required"}), 400

    existing = Target.query.filter_by(user_id=g.current_user.id, url=url).first()
    if existing:
        return jsonify({"status": "fail", "message": "You are already tracking this URL"}), 409

    target = Target(name=name, url=url, status="Pending", user_id=g.current_user.id)
    db.session.add(target)
    db.session.commit()

    # Perform initial check immediately
    res = check_url(url)
    target.status = res["status"]
    create_log_from_result(target.id, res)
    db.session.commit()

    return jsonify({
        "id": target.id,
        "name": target.name,
        "url": target.url,
        "status": target.status,
        "user_id": target.user_id,
        "initial_check": res
    }), 201


@targets_bp.route("/api/targets/<int:id>", methods=["DELETE"])
@token_required
def delete_target(id):
    target = Target.query.filter_by(id=id, user_id=g.current_user.id).first()
    if not target:
        return jsonify({"status": "fail", "message": "Target not found or unauthorized"}), 404

    db.session.delete(target)
    db.session.commit()
    return jsonify({"status": "success", "message": "Target deleted successfully"}), 200


@targets_bp.route("/api/targets/<int:id>/logs", methods=["GET"])
@token_required
def get_target_logs(id):
    target = Target.query.filter_by(id=id, user_id=g.current_user.id).first()
    if not target:
        return jsonify({"status": "fail", "message": "Target not found or unauthorized"}), 404

    logs = Log.query.filter_by(target_id=target.id).order_by(Log.timestamp.desc()).all()

    return jsonify({
        "target": {"id": target.id, "name": target.name, "url": target.url},
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat(),
                "status": l.status,
                "response_time": l.response_time,
                "status_code": l.status_code,
                "error_message": l.error_message,
                "details": l.details,
            }
            for l in logs
        ],
    }), 200


@targets_bp.route("/api/targets/<int:id>/ping", methods=["POST"])
@token_required
def ping_target(id):
    """Manually ping a single target -- updates its status and saves a log entry."""
    target = Target.query.filter_by(id=id, user_id=g.current_user.id).first()
    if not target:
        return jsonify({"status": "fail", "message": "Target not found or unauthorized"}), 404

    res = check_url(target.url)
    target.status = res["status"]
    create_log_from_result(target.id, res)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Ping {res['status']}",
        "data": res
    }), 200
