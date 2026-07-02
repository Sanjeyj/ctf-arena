import uuid as _uuid
from app.extensions import db
from app.models.mixins import TimestampMixin


class AIConversation(db.Model, TimestampMixin):
    """Stores free-form AI chat exchanges between users and the assistant."""
    __tablename__ = 'ai_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='SET NULL'),
                             nullable=True, index=True)

    session_id = db.Column(db.String(36), default=lambda: str(_uuid.uuid4()), nullable=False, index=True)

    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    tokens_used = db.Column(db.Integer, default=0, nullable=False)

    provider = db.Column(db.String(50), default='stub', nullable=False)
    model_name = db.Column(db.String(100), nullable=True)

    user = db.relationship('User', backref=db.backref('ai_conversations', lazy='dynamic'))
    challenge = db.relationship('Challenge', backref=db.backref('ai_conversations', lazy='dynamic'))
