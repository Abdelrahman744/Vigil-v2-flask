"""
Vigil — Utility Functions
=========================
Helper functions: URL checking, JWT token generation, and auth decorators.
"""

import time
import datetime
from functools import wraps

import requests as http_requests
import jwt as pyjwt
from flask import request, jsonify, g, current_app

from app import db
from app.models import User


# ---------------------------------------------------------------------------
# Monitoring Helper
# ---------------------------------------------------------------------------

def check_url(url: str) -> dict:
    """Pings a URL and returns its status, response time, and status code."""
    start_time = time.time()
    try:
        # Avoid caching, and mimic a real browser to prevent basic blocks
        headers = {'User-Agent': 'Vigil-Uptime-Monitor/2.0'}
        response = http_requests.get(url, headers=headers, timeout=10)
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
    except http_requests.exceptions.RequestException as e:
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

_blacklisted_tokens: set = set()


def generate_token(user_id: int) -> str:
    """Create a JWT token valid for 30 days."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user_id,
        "exp": now + datetime.timedelta(days=30),
        "iat": now,
    }
    return pyjwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def token_required(f):
    """Decorator that enforces Bearer-token authentication on a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"status": "fail", "message": "Token is missing"}), 401

        if token in _blacklisted_tokens:
            return jsonify({"status": "fail", "message": "Token has been revoked"}), 401

        try:
            data = pyjwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            g.current_user = db.session.get(User, data["user_id"])
            if g.current_user is None:
                raise ValueError("User not found")
        except pyjwt.ExpiredSignatureError:
            return jsonify({"status": "fail", "message": "Token has expired"}), 401
        except Exception:
            return jsonify({"status": "fail", "message": "Token is invalid"}), 401

        return f(*args, **kwargs)
    return decorated


def blacklist_token(token: str):
    """Add a token to the in-memory blacklist."""
    _blacklisted_tokens.add(token)


def create_log_from_result(target_id: int, result: dict):
    """Create a Log entry from a check_url result dict and add it to the session."""
    from app.models import Log
    log = Log(
        target_id=target_id,
        status=result["status"],
        response_time=result["response_time"],
        status_code=result["status_code"],
        error_message=result["error_message"],
        details=result["details"]
    )
    db.session.add(log)
    return log
