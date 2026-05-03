"""
Vigil — Flask REST API
======================
A lightweight website-uptime tracking backend powered by Flask + SQLite.
Provides user registration/login (JWT), CRUD for monitoring targets,
and a log history per target.
"""

import os
import datetime

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt as pyjwt  # PyJWT

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "vigil-super-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI", "sqlite:///vigil.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app, supports_credentials=True)
db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(db.Model):
    """Registered application user."""
    __tablename__ = "user"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    targets = db.relationship("Target", backref="owner", lazy=True,
                              cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Target(db.Model):
    """A website URL being monitored by a specific user."""
    __tablename__ = "target"

    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(200), nullable=False)
    url     = db.Column(db.String(2048), nullable=False)
    status  = db.Column(db.String(20), default="Unknown")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    logs = db.relationship("Log", backref="target", lazy=True,
                           cascade="all, delete-orphan")

    # Composite unique: same user cannot track the same URL twice,
    # but different users CAN track the same URL.
    __table_args__ = (
        db.UniqueConstraint("user_id", "url", name="uq_user_url"),
    )


class Log(db.Model):
    """Historical check result for a given target."""
    __tablename__ = "log"

    id        = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey("target.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    details   = db.Column(db.Text, default="")


# ---------------------------------------------------------------------------
# JWT Authentication Helpers
# ---------------------------------------------------------------------------

def generate_token(user_id: int) -> str:
    """Create a JWT token valid for 30 days."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user_id,
        "exp": now + datetime.timedelta(days=30),
        "iat": now,
    }
    return pyjwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def token_required(f):
    """Decorator that protects a route with JWT Bearer token authentication."""
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


# ---------------------------------------------------------------------------
# Blacklist for logout (in-memory; use Redis/DB for production)
# ---------------------------------------------------------------------------
_blacklisted_tokens: set = set()


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

# ── 1. POST /api/register ─────────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"status": "fail",
                        "message": "username, email, and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"status": "fail",
                        "message": "Username already exists"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"status": "fail",
                        "message": "Email already registered"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id)
    return jsonify({
        "status": "success",
        "token": token,
        "data": {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }
    }), 201


# ── 2. POST /api/login ────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT token."""
    data = request.get_json(silent=True) or {}

    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"status": "fail",
                        "message": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"status": "fail",
                        "message": "Incorrect email or password"}), 401

    token = generate_token(user.id)
    return jsonify({"status": "success", "token": token}), 200


# ── 3. POST /api/logout ───────────────────────────────────────────────────
@app.route("/api/logout", methods=["POST"])
@token_required
def logout():
    """Invalidate the current JWT token (blacklist)."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1]
    _blacklisted_tokens.add(token)
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200


# ── 4. GET /api/targets ───────────────────────────────────────────────────
@app.route("/api/targets", methods=["GET"])
@token_required
def get_targets():
    """List all tracking targets belonging to the authenticated user."""
    targets = Target.query.filter_by(user_id=g.current_user.id)\
                          .order_by(Target.id.desc()).all()

    result = []
    for t in targets:
        latest_log = Log.query.filter_by(target_id=t.id)\
                              .order_by(Log.timestamp.desc()).first()
        result.append({
            "id": t.id,
            "name": t.name,
            "url": t.url,
            "status": t.status,
            "user_id": t.user_id,
            "last_checked": latest_log.timestamp.isoformat() if latest_log else None,
        })

    return jsonify({"count": len(result), "targets": result}), 200


# ── 5. POST /api/targets ──────────────────────────────────────────────────
@app.route("/api/targets", methods=["POST"])
@token_required
def add_target():
    """Add a new tracking target for the authenticated user."""
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    url  = data.get("url", "").strip()

    if not name or not url:
        return jsonify({"status": "fail",
                        "message": "name and url are required"}), 400

    # Check composite uniqueness
    existing = Target.query.filter_by(user_id=g.current_user.id, url=url).first()
    if existing:
        return jsonify({"status": "fail",
                        "message": "You are already tracking this URL"}), 409

    target = Target(name=name, url=url, status="Pending", user_id=g.current_user.id)
    db.session.add(target)
    db.session.commit()

    # Create an initial log entry
    initial_log = Log(target_id=target.id, details="Target created — awaiting first check")
    db.session.add(initial_log)
    db.session.commit()

    return jsonify({
        "id": target.id,
        "name": target.name,
        "url": target.url,
        "status": target.status,
        "user_id": target.user_id,
    }), 201


# ── 6. DELETE /api/targets/<id> ───────────────────────────────────────────
@app.route("/api/targets/<int:id>", methods=["DELETE"])
@token_required
def delete_target(id):
    """Delete a specific target (and its logs) belonging to the authenticated user."""
    target = Target.query.filter_by(id=id, user_id=g.current_user.id).first()

    if not target:
        return jsonify({"status": "fail",
                        "message": "Target not found or unauthorized"}), 404

    db.session.delete(target)  # cascade deletes associated logs
    db.session.commit()

    return jsonify({"status": "success",
                    "message": "Target deleted successfully"}), 200


# ── 7. GET /api/targets/<id>/logs ─────────────────────────────────────────
@app.route("/api/targets/<int:id>/logs", methods=["GET"])
@token_required
def get_target_logs(id):
    """Retrieve the check-history (logs) for a specific target."""
    target = Target.query.filter_by(id=id, user_id=g.current_user.id).first()

    if not target:
        return jsonify({"status": "fail",
                        "message": "Target not found or unauthorized"}), 404

    logs = Log.query.filter_by(target_id=target.id)\
                    .order_by(Log.timestamp.desc()).all()

    return jsonify({
        "target": {"id": target.id, "name": target.name, "url": target.url},
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat(),
                "details": l.details,
            }
            for l in logs
        ],
    }), 200


# ---------------------------------------------------------------------------
# Health-check (non-authenticated)
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Vigil API is running ✅"}), 200


# ---------------------------------------------------------------------------
# Database Initialisation & Entry Point
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
