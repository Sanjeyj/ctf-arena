from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class ChallengeFile(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'challenge_files'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False, index=True)
    location = db.Column(db.String(255), nullable=False) # Backwards compatibility target path
    
    # Extended CMS Fields
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, default=0, nullable=False)
    checksum = db.Column(db.String(64), nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    download_count = db.Column(db.Integer, default=0, nullable=False)
