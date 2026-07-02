from app.extensions import db
from app.models.mixins import TimestampMixin


class AIWriteup(db.Model, TimestampMixin):
    """Stores AI-generated educational writeups for challenges."""
    __tablename__ = 'ai_writeups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False, index=True)

    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    tokens_used = db.Column(db.Integer, default=0, nullable=False)

    provider = db.Column(db.String(50), default='stub', nullable=False)
    model_name = db.Column(db.String(100), nullable=True)

    # Content breakdown
    summary = db.Column(db.Text, nullable=True)
    steps = db.Column(db.Text, nullable=True)
    learning_points = db.Column(db.Text, nullable=True)

    # Admin approval workflow: draft → approved → published
    status = db.Column(db.String(20), default='draft', nullable=False, index=True)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    published = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('ai_writeups', lazy='dynamic'))
    challenge = db.relationship('Challenge', backref=db.backref('ai_writeups', lazy='dynamic'))
