from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DecisionContext(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'decision_contexts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    context_type = db.Column(db.String(64), nullable=False)  # risk, resilience, compliance, architecture, operations, investment, trust, incident
    business_scope = db.Column(db.String(128), nullable=True)
    risk_score = db.Column(db.Float, default=0.0)
    resilience_score = db.Column(db.Float, default=0.0)
    control_effectiveness_score = db.Column(db.Float, default=0.0)
    evidence_confidence_score = db.Column(db.Float, default=0.0)
    urgency_score = db.Column(db.Float, default=0.0)
    context_json = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='active')  # active, review, archived

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'context_type': self.context_type,
            'business_scope': self.business_scope,
            'risk_score': self.risk_score,
            'resilience_score': self.resilience_score,
            'control_effectiveness_score': self.control_effectiveness_score,
            'evidence_confidence_score': self.evidence_confidence_score,
            'urgency_score': self.urgency_score,
            'context_json': self.context_json,
            'status': self.status,
            'organization_id': self.organization_id
        }
