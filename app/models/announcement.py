from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin
import datetime

class Announcement(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    scheduled_at = db.Column(db.DateTime, nullable=True)
    pinned = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    published = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
    visibility = db.Column(db.String(20), default="public", nullable=False, server_default='public')
