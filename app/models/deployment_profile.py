import datetime
from app.extensions import db, utcnow

class DeploymentProfile(db.Model):
    __tablename__ = 'deployment_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    # Resource limits
    cpu_limit = db.Column(db.Float, default=0.5, nullable=False)   # CPU cores
    memory_limit = db.Column(db.String(20), default='128m', nullable=False)  # e.g. '128m', '1g'
    pids_limit = db.Column(db.Integer, default=64, nullable=False)
    network_disabled = db.Column(db.Boolean, default=False, nullable=False)

    # TTL & port settings
    ttl_minutes = db.Column(db.Integer, default=30, nullable=False)   # Instance lifetime in minutes
    max_instances_per_user = db.Column(db.Integer, default=1, nullable=False)
    port_range_start = db.Column(db.Integer, default=10000, nullable=False)
    port_range_end = db.Column(db.Integer, default=20000, nullable=False)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    instances = db.relationship('ChallengeInstance', backref='deployment_profile', lazy=True)
