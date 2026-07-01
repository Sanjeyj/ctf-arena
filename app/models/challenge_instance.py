import datetime
from app.extensions import db

class ChallengeInstance(db.Model):
    __tablename__ = 'challenge_instances'

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, index=True)
    docker_image_id = db.Column(db.Integer, db.ForeignKey('docker_images.id', ondelete='SET NULL'), nullable=True)
    deployment_profile_id = db.Column(db.Integer, db.ForeignKey('deployment_profiles.id', ondelete='SET NULL'), nullable=True)

    container_id = db.Column(db.String(64), nullable=True)
    hostname = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    mapped_port = db.Column(db.Integer, nullable=True, index=True)
    status = db.Column(db.String(20), default='stopped', nullable=False, index=True)
    # statuses: creating, running, stopped, expired, error, destroyed

    started_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    stopped_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    logs = db.relationship('ContainerLog', backref='instance', lazy=True, cascade='all, delete-orphan')
    snapshots = db.relationship('InstanceSnapshot', backref='instance', lazy=True, cascade='all, delete-orphan')
