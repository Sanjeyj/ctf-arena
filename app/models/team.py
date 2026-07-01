from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin, SoftDeleteMixin
import datetime

class Team(db.Model, TimestampMixin, UUIDMixin, SoftDeleteMixin):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    users = db.relationship('User', backref='team', lazy=True)
    competitions = db.relationship('Competition', secondary='team_competitions', backref='teams', lazy=True)

