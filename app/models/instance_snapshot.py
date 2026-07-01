import datetime
from app.extensions import db, utcnow

class InstanceSnapshot(db.Model):
    __tablename__ = 'instance_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('challenge_instances.id', ondelete='CASCADE'), nullable=False, index=True)
    snapshot_name = db.Column(db.String(100), nullable=False)
    image_ref = db.Column(db.String(255), nullable=True)  # Docker image ref or sim key
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
