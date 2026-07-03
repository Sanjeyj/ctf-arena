"""
EnterpriseGoal model - Phase 26 Autonomous Cyber Enterprise.
Measures long-term strategic resilience goals and security objectives.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class EnterpriseGoal(db.Model, TimestampMixin, TenantMixin):
    """Strategic compliance / security objective goal."""
    __tablename__ = 'enterprise_goals'

    id = db.Column(db.Integer, primary_key=True)
    objective = db.Column(db.String(255), nullable=False)
    target_score = db.Column(db.Float, default=90.0, nullable=False)
    progress = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False) # active, completed

    def __repr__(self):
        return f'<EnterpriseGoal {self.objective[:30]} target={self.target_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'objective': self.objective,
            'target_score': self.target_score,
            'progress': self.progress,
            'status': self.status,
            'organization_id': self.organization_id
        }
