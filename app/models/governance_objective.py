from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class GovernanceObjective(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'governance_objectives'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    objective_type = db.Column(db.String(64), nullable=False)  # risk_reduction, resilience, compliance, assurance, reliability, exposure_reduction, validation_effectiveness, investment_efficiency
    description = db.Column(db.Text, nullable=True)
    target_score = db.Column(db.Float, default=0.0)
    current_score = db.Column(db.Float, default=0.0)
    weight = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.String(64), nullable=True)
    owner = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(32), default='proposed')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'objective_type': self.objective_type,
            'description': self.description,
            'target_score': self.target_score,
            'current_score': self.current_score,
            'weight': self.weight,
            'deadline': self.deadline,
            'owner': self.owner,
            'status': self.status,
            'organization_id': self.organization_id
        }
