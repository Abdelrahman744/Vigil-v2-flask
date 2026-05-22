"""
Vigil — Auth Routes
===================
/api/register, /api/login, /api/logout
"""

from flask import Blueprint, request, jsonify

from model import db, User
from utils import generate_token, token_required, blacklist_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"status": "fail", "message": "username, email, and password are required"}), 400

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


@auth_bp.route("/api/login", methods=["POST"])
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


@auth_bp.route("/api/logout", methods=["POST"])
@token_required
def logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1]
    blacklist_token(token)
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200
