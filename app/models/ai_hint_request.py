from app.extensions import db
from app.models.mixins import TimestampMixin


class AIHintRequest(db.Model, TimestampMixin):
    """Tracks every AI-generated hint request made by users."""
    __tablename__ = 'ai_hint_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False, index=True)

    hint_level = db.Column(db.Integer, default=1, nullable=False)  # 1, 2, or 3
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    tokens_used = db.Column(db.Integer, default=0, nullable=False)

    provider = db.Column(db.String(50), default='stub', nullable=False)
    model_name = db.Column(db.String(100), nullable=True)
    cost_deducted = db.Column(db.Integer, default=0, nullable=False)  # points deducted
    success = db.Column(db.Boolean, default=True, nullable=False)

    user = db.relationship('User', backref=db.backref('ai_hint_requests', lazy='dynamic'))
    challenge = db.relationship('Challenge', backref=db.backref('ai_hint_requests', lazy='dynamic'))
