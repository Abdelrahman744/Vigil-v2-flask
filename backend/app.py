"""
Vigil — Application Entry & Factory
====================================
Creates and configures the Flask application and manages the background cron heartbeat.
"""

import os
import time
import threading
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from model import db
from dotenv import load_dotenv


def create_app():
    """Application factory: builds, configures, and returns the Flask app."""
    app = Flask(__name__)

    # Load environment files
    basedir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(basedir, ".flaskenv"))
    load_dotenv(os.path.join(basedir, "secret.env"))

    # Configure application parameters
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "vigil-super-secret-key-change-me")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URI", f"sqlite:///{os.path.join(basedir, 'instance', 'vigil.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialise extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.targets import targets_bp
    from routes.monitor import monitor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(targets_bp)
    app.register_blueprint(monitor_bp)

    # Health-check root route
    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "Vigil API is running ✅"}), 200

    # Create database tables
    basedir = os.path.abspath(os.path.dirname(__file__))
    with app.app_context():
        os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
        import model  # noqa: F401 — ensure models are imported before create_all
        db.create_all()

    return app


def start_heartbeat_loop():
    """Background thread that triggers the heartbeat every 60 seconds."""
    while True:
        time.sleep(60)
        try:
            print("\n[Vigil Cron] Triggering background heartbeat...")
            res = requests.get("http://127.0.0.1:5000/api/cron/heartbeat", timeout=60)
            data = res.json()
            print(f"[Vigil Cron] Heartbeat complete  — Checked {data.get('checked', 0)} targets.")
            for r in data.get("results", []):
                icon = "[UP]" if r['status'] == 'Up' else "[DOWN]"
                print(f"  {icon} Target {r['id']} ({r['name']}): {r['status']} ({r['latency']}ms)")
            print()
        except Exception as e:
            print(f"\n[Vigil Cron] Heartbeat failed [FAIL]: {e}\n")


app = create_app()

if __name__ == "__main__":
    # Start the heartbeat loop only in the Werkzeug worker process to avoid duplication
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        monitor_thread = threading.Thread(target=start_heartbeat_loop, daemon=True)
        monitor_thread.start()

    app.run(host="0.0.0.0", port=5000, debug=True)
