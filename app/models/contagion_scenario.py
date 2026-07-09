"""
ContagionScenario model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Defines a simulation-only contagion propagation scenario starting from an
initial node. Strictly offline — no external communication.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ContagionScenario(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'contagion_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scenario_type = db.Column(db.String(64), nullable=False)
    # shared_service_failure, vendor_failure, cloud_region_disruption,
    # identity_provider_failure, supply_chain_disruption,
    # coordinated_campaign_simulation, multi_region_failure,
    # correlated_dependency_failure
    initial_node_id = db.Column(db.Integer, db.ForeignKey('systemic_risk_nodes.id', ondelete='SET NULL'), nullable=True)
    severity = db.Column(db.String(32), default='high')         # low, medium, high, critical
    initial_impact_score = db.Column(db.Float, default=50.0)    # 0-100
    propagation_depth = db.Column(db.Integer, default=5)        # max hops
    correlation_factor = db.Column(db.Float, default=0.5)       # 0-1
    configuration_json = db.Column(db.Text, default='{}')
    random_seed = db.Column(db.Integer, default=42)
    status = db.Column(db.String(32), default='draft')
    # draft, active, archived

    initial_node = db.relationship('SystemicRiskNode', foreign_keys=[initial_node_id],
                                   backref=db.backref('contagion_scenarios', lazy='dynamic'))
    simulation_runs = db.relationship('ContagionSimulationRun',
                                      backref=db.backref('scenario', lazy='joined'),
                                      cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        db.Index('ix_contagion_scenario_org', 'organization_id'),
        db.Index('ix_contagion_scenario_initial_node', 'initial_node_id'),
    )

    def __repr__(self):
        return f'<ContagionScenario {self.name!r} type={self.scenario_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scenario_type': self.scenario_type,
            'initial_node_id': self.initial_node_id,
            'severity': self.severity,
            'initial_impact_score': self.initial_impact_score,
            'propagation_depth': self.propagation_depth,
            'correlation_factor': self.correlation_factor,
            'random_seed': self.random_seed,
            'status': self.status,
            'organization_id': self.organization_id,
        }
