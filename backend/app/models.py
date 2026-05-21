"""
Vigil — SQLAlchemy Models
=========================
User, Target, and Log models for the uptime monitoring database.
"""

import datetime
from typing import Optional
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = "user"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    targets = db.relationship("Target", backref="owner", lazy=True, cascade="all, delete-orphan")

    def __init__(self, username: str = "", email: str = "", password_hash: str = ""):
        self.username = username
        self.email = email
        self.password_hash = password_hash

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

    def __init__(self, name: str = "", url: str = "", status: str = "Pending",
                 user_id: int = 0):
        self.name = name
        self.url = url
        self.status = status
        self.user_id = user_id


class Log(db.Model):
    __tablename__ = "log"
    id            = db.Column(db.Integer, primary_key=True)
    target_id     = db.Column(db.Integer, db.ForeignKey("target.id"), nullable=False)
    timestamp     = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    status        = db.Column(db.String(20), default="Pending")
    response_time = db.Column(db.Integer, default=0)  # milliseconds
    status_code   = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    details       = db.Column(db.Text, default="")

    def __init__(self, target_id: int = 0, status: str = "Pending",
                 response_time: int = 0, status_code: Optional[int] = None,
                 error_message: Optional[str] = None, details: str = ""):
        self.target_id = target_id
        self.status = status
        self.response_time = response_time
        self.status_code = status_code
        self.error_message = error_message
        self.details = details
