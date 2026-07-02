from app.extensions import db, utcnow
from app.models.mixins import TimestampMixin, UUIDMixin, SoftDeleteMixin, TenantMixin
import datetime

class Team(db.Model, TimestampMixin, UUIDMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'teams'

    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    users = db.relationship('User', backref='team', lazy=True)
    competitions = db.relationship('Competition', secondary='team_competitions', backref='teams', lazy=True)

