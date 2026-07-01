import datetime
from app.extensions import db, utcnow

class ContainerLog(db.Model):
    __tablename__ = 'container_logs'

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('challenge_instances.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    level = db.Column(db.String(20), default='info', nullable=False)
    # levels: info, warn, error, debug
    message = db.Column(db.Text, nullable=False)
