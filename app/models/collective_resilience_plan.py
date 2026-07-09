"""
CollectiveResiliencePlan model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Simulation-only resilience plan requiring explicit human approval before activation.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CollectiveResiliencePlan(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'collective_resilience_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    scope = db.Column(db.String(120), nullable=True)
    plan_type = db.Column(db.String(64), nullable=False)
    # dependency_diversification, shared_recovery, mutual_aid_simulation,
    # collective_control, sector_resilience, regional_resilience, shared_service_recovery
    participating_nodes_json = db.Column(db.Text, default='[]')
    baseline_resilience_score = db.Column(db.Float, default=0.0)            # 0-100
    target_resilience_score = db.Column(db.Float, default=0.0)              # 0-100
    estimated_cost = db.Column(db.Float, default=0.0)
    expected_systemic_risk_reduction = db.Column(db.Float, default=0.0)     # 0-100
    priority_score = db.Column(db.Float, default=0.0)                       # 0-100
    approval_status = db.Column(db.String(32), default='pending')
    # pending, approved, rejected
    status = db.Column(db.String(32), default='draft')
    # draft, active, completed, archived

    __table_args__ = (
        db.Index('ix_collective_plan_org', 'organization_id'),
    )

    def __repr__(self):
        return f'<CollectiveResiliencePlan {self.name!r} type={self.plan_type}>'

    def to_dict(self):
        import json
        try:
            nodes = json.loads(self.participating_nodes_json or '[]')
        except Exception:
            nodes = []
        return {
            'id': self.id,
            'name': self.name,
            'scope': self.scope,
            'plan_type': self.plan_type,
            'participating_nodes': nodes,
            'baseline_resilience_score': self.baseline_resilience_score,
            'target_resilience_score': self.target_resilience_score,
            'estimated_cost': self.estimated_cost,
            'expected_systemic_risk_reduction': self.expected_systemic_risk_reduction,
            'priority_score': self.priority_score,
            'approval_status': self.approval_status,
            'status': self.status,
            'organization_id': self.organization_id,
        }
