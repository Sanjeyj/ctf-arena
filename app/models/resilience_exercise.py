"""
ResilienceExercise model - Phase 25 Cyber Resilience & Digital Enterprise.
Logs disaster preparedness tabletop exercises, drills, simulations, and lessons learned.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ResilienceExercise(db.Model, TimestampMixin, TenantMixin):
    """Tabletop and simulation drill logs."""
    __tablename__ = 'resilience_exercises'

    id = db.Column(db.Integer, primary_key=True)
    exercise_type = db.Column(db.String(64), default='tabletop', nullable=False) # tabletop, simulation, drill
    results = db.Column(db.Text, nullable=True)
    lessons_learned = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, default=0.0, nullable=False) # 0.0 - 100.0

    def __repr__(self):
        return f'<ResilienceExercise {self.exercise_type!r} score={self.score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'exercise_type': self.exercise_type,
            'results': self.results,
            'lessons_learned': self.lessons_learned,
            'score': self.score,
            'organization_id': self.organization_id
        }
