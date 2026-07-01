from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Certificate(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='SET NULL'), nullable=True, index=True)
    hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
