"""
Vigil — Monitor Routes
======================
/api/cron/heartbeat — scheduled monitoring for all targets.
"""

from flask import Blueprint, jsonify

from app import db
from app.models import Target
from app.utils import check_url, create_log_from_result

monitor_bp = Blueprint("monitor", __name__)


@monitor_bp.route("/api/cron/heartbeat", methods=["GET"])
def cron_heartbeat():
    """Background job endpoint to check ALL targets. Triggered by Vercel Cron."""
    targets = Target.query.all()
    results = []

    for t in targets:
        res = check_url(t.url)
        t.status = res["status"]
        create_log_from_result(t.id, res)
        results.append({"id": t.id, "name": t.name, "url": t.url, "status": res["status"], "latency": res["response_time"]})

    db.session.commit()
    return jsonify({"message": "Heartbeat completed", "checked": len(results), "results": results}), 200
