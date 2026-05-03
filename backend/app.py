"""
Vigil — Flask REST API
======================
A lightweight website-uptime tracking backend powered by Flask + SQLite.
Provides user registration/login (JWT), CRUD for monitoring targets,
and real-time monitoring via requests.
"""

import os
import time
import datetime
import requests

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt as pyjwt

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "vigil-super-secret-key-change-me")
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URI", f"sqlite:///{os.path.join(basedir, 'instance', 'vigil.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app, supports_credentials=True)
db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(db.Model):
    __tablename__ = "user"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    targets = db.relationship("Target", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Target(db.Model):
    __tablename__ = "target"
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(200), nullable=False)
    url     = db.Column(db.String(2048), nullable=False)
    status  = db.Column(db.String(20), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    logs = db.relationship("Log", backref="target", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("user_id", "url", name="uq_user_url"),
    )


class Log(db.Model):
    __tablename__ = "log"
    id            = db.Column(db.Integer, primary_key=True)
    target_id     = db.Column(db.Integer, db.ForeignKey("target.id"), nullable=False)
    timestamp     = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    status        = db.Column(db.String(20), default="Pending")
    response_time = db.Column(db.Integer, default=0) # milliseconds
    status_code   = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    details       = db.Column(db.Text, default="")

# ---------------------------------------------------------------------------
# Monitoring Helper
# ---------------------------------------------------------------------------

def check_url(url: str) -> dict:
    """Pings a URL and returns its status, response time, and status code."""
    start_time = time.time()
    try:
        # Avoid caching, and mimic a real browser to prevent basic blocks
        headers = {'User-Agent': 'Vigil-Uptime-Monitor/2.0'}
        response = requests.get(url, headers=headers, timeout=10)
        duration = int((time.time() - start_time) * 1000)
        
        # Consider 2xx and 3xx as Up
        is_up = 200 <= response.status_code < 400
        
        return {
            "status": "Up" if is_up else "Down",
            "response_time": duration,
            "status_code": response.status_code,
            "error_message": None if is_up else f"HTTP {response.status_code}",
            "details": f"Check completed in {duration}ms (Status: {response.status_code})"
        }
    except requests.exceptions.RequestException as e:
        duration = int((time.time() - start_time) * 1000)
        status_code = None
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            
        return {
            "status": "Down",
            "response_time": duration,
            "status_code": status_code,
            "error_message": str(e),
            "details": f"Check failed after {duration}ms. Error: {str(e)}"
        }

# ---------------------------------------------------------------------------
# JWT Authentication Helpers
# ---------------------------------------------------------------------------

def generate_token(user_id: int) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user_id,
        "exp": now + datetime.timedelta(days=30),
        "iat": now,
    }
    return pyjwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"status": "fail", "message": "Token is missing"}), 401

        try:
            data = pyjwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            g.current_user = db.session.get(User, data["user_id"])
            if g.current_user is None:
                raise ValueError("User not found")
        except pyjwt.ExpiredSignatureError:
            return jsonify({"status": "fail", "message": "Token has expired"}), 401
        except Exception:
            return jsonify({"status": "fail", "message": "Token is invalid"}), 401

        return f(*args, **kwargs)
    return decorated

_blacklisted_tokens: set = set()

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"status": "fail", "message": "username, email, and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"status": "fail", "message": "Username already exists"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"status": "fail", "message": "Email already registered"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "status": "success",
        "token": generate_token(user.id),
        "data": {"user": {"id": user.id, "username": user.username, "email": user.email}}
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"status": "fail", "message": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"status": "fail", "message": "Incorrect email or password"}), 401

    return jsonify({"status": "success", "token": generate_token(user.id)}), 200


@app.route("/api/logout", methods=["POST"])
@token_required
def logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1]
    _blacklisted_tokens.add(token)
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200


@app.route("/api/targets", methods=["GET"])
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


@app.route("/api/targets", methods=["POST"])
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
    
    log = Log(
        target_id=target.id,
        status=res["status"],
        response_time=res["response_time"],
        status_code=res["status_code"],
        error_message=res["error_message"],
        details=res["details"]
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "id": target.id,
        "name": target.name,
        "url": target.url,
        "status": target.status,
        "user_id": target.user_id,
        "initial_check": res
    }), 201


@app.route("/api/targets/<int:id>", methods=["DELETE"])
@token_required
def delete_target(id):
    target = Target.query.filter_by(id=id, user_id=g.current_user.id).first()
    if not target:
        return jsonify({"status": "fail", "message": "Target not found or unauthorized"}), 404

    db.session.delete(target)
    db.session.commit()
    return jsonify({"status": "success", "message": "Target deleted successfully"}), 200


@app.route("/api/targets/<int:id>/logs", methods=["GET"])
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


# ── Monitoring & Manual Pings ─────────────────────────────────────────────

@app.route("/api/ping", methods=["POST"])
@token_required
def ping_website():
    """Manually check a URL on demand (doesn't save to DB, useful for frontend test button)."""
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url:
         return jsonify({"message": "url is required"}), 400
    res = check_url(url)
    return jsonify({"message": f"Ping {res['status']}", "data": res}), 200 if res["status"] == "Up" else 500


@app.route("/api/cron/heartbeat", methods=["GET"])
def cron_heartbeat():
    """Background job endpoint to check ALL targets. Triggered by Vercel Cron."""
    # In production, check for a secret header from Vercel to protect this route
    targets = Target.query.all()
    results = []
    
    for t in targets:
        res = check_url(t.url)
        t.status = res["status"]
        
        log = Log(
            target_id=t.id,
            status=res["status"],
            response_time=res["response_time"],
            status_code=res["status_code"],
            error_message=res["error_message"],
            details=res["details"]
        )
        db.session.add(log)
        results.append({"id": t.id, "url": t.url, "status": res["status"], "latency": res["response_time"]})
    
    db.session.commit()
    return jsonify({"message": "Heartbeat completed", "checked": len(results), "results": results}), 200


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Vigil API is running ✅"}), 200

# ---------------------------------------------------------------------------
# Database Initialisation & Entry Point
# ---------------------------------------------------------------------------
with app.app_context():
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
