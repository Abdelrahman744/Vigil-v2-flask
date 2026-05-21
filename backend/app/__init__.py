"""
Vigil — Application Factory
============================
Creates and configures the Flask application using the factory pattern.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    """Application factory: builds, configures, and returns the Flask app."""
    app = Flask(__name__)

    # Load config
    from config import Config
    app.config.from_object(Config)

    # Initialise extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.targets import targets_bp
    from app.routes.monitor import monitor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(targets_bp)
    app.register_blueprint(monitor_bp)

    # Health-check root route
    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "Vigil API is running ✅"}), 200

    # Create database tables
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    with app.app_context():
        os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
        from app import models  # noqa: F401 — ensure models are imported before create_all
        db.create_all()

    return app
