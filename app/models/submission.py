from app.extensions import db, utcnow
from app.models.mixins import TimestampMixin, UUIDMixin
import datetime

class Submission(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False, index=True)
    
    points = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, default=utcnow, nullable=False)
    elapsed = db.Column(db.Integer, nullable=True) # time elapsed since registration
    
    submitted_flag = db.Column(db.String(255), nullable=True)
    correct = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
    status = db.Column(db.String(20), default="correct", nullable=False, server_default='correct') # correct, wrong, duplicate, rejected
