from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Tag(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

class ChallengeTag(db.Model, TimestampMixin):
    __tablename__ = 'challenge_tags'
    
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
