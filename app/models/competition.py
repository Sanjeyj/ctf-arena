from app.extensions import db, utcnow
from app.models.mixins import TimestampMixin, UUIDMixin
import datetime

# Association Table for Team-Competition Many-to-Many
team_competitions = db.Table('team_competitions',
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True),
    db.Column('competition_id', db.Integer, db.ForeignKey('competitions.id', ondelete='CASCADE'), primary_key=True)
)

class Competition(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'competitions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    registration_open = db.Column(db.DateTime, nullable=True)
    registration_close = db.Column(db.DateTime, nullable=True)
    freeze_time = db.Column(db.DateTime, nullable=True)
    unfreeze_time = db.Column(db.DateTime, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
    is_paused = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    is_archived = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    
    visibility = db.Column(db.String(20), default="public", nullable=False, server_default='public')
    allow_practice = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
    max_attempts = db.Column(db.Integer, default=0, nullable=False, server_default='0')
    
    rules = db.Column(db.Text, nullable=True)
    banner = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    challenges = db.relationship('Challenge', backref='competition', lazy=True, cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='competition', lazy=True, cascade='all, delete-orphan')
