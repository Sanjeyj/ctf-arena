from app.extensions import db
from app.models.mixins import TimestampMixin


class AIDifficultyPrediction(db.Model, TimestampMixin):
    """Stores AI-predicted difficulty ratings for challenges."""
    __tablename__ = 'ai_difficulty_predictions'

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='CASCADE'),
                             nullable=False, index=True)

    # Input features snapshot
    solve_count = db.Column(db.Integer, default=0, nullable=False)
    wrong_attempts = db.Column(db.Integer, default=0, nullable=False)
    avg_solve_time_seconds = db.Column(db.Float, default=0.0, nullable=False)
    hint_usage_count = db.Column(db.Integer, default=0, nullable=False)

    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    tokens_used = db.Column(db.Integer, default=0, nullable=False)

    # Prediction output
    predicted_difficulty = db.Column(db.String(20), nullable=True)  # Easy, Medium, Hard, Insane
    confidence_score = db.Column(db.Float, default=0.0, nullable=False)
    explanation = db.Column(db.Text, nullable=True)

    provider = db.Column(db.String(50), default='stub', nullable=False)
    model_name = db.Column(db.String(100), nullable=True)

    challenge = db.relationship('Challenge', backref=db.backref('ai_difficulty_predictions', lazy='dynamic'))
