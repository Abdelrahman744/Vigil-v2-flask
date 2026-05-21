"""
Vigil — Configuration
=====================
Centralised configuration variables for the Flask application.
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "vigil-super-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI", f"sqlite:///{os.path.join(basedir, 'instance', 'vigil.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
