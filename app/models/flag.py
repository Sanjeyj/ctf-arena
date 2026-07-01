from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Flag(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'flags'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.String(255), nullable=False)
    flag_type = db.Column(db.String(20), default='exact', nullable=False) # exact, regex, hashed
    
    # Extended CMS Fields
    is_case_sensitive = db.Column(db.Boolean, default=True, nullable=False)
    priority = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
