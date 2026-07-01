from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Hint(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'hints'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer, default=0, nullable=False)
    
    # Extended CMS Fields
    title = db.Column(db.String(100), nullable=True)
    visible = db.Column(db.Boolean, default=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    
    unlocks = db.relationship('HintUnlock', backref='hint', lazy=True, cascade='all, delete-orphan')

class HintUnlock(db.Model, TimestampMixin):
    __tablename__ = 'hint_unlocks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    hint_id = db.Column(db.Integer, db.ForeignKey('hints.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('hint_unlocks', lazy=True, cascade='all, delete-orphan'))
