"""
ChaosExperiment model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Stores simulated chaos engineering test metadata and outcomes.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ChaosExperiment(db.Model, TimestampMixin, TenantMixin):
    """ChaosExperiment model."""
    __tablename__ = 'chaos_experiments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    experiment_type = db.Column(db.String(64), nullable=False)  # latency_injection, packet_loss, dependency_failure
    target_service = db.Column(db.String(120), nullable=False)  # service name or reference
    hypothesis = db.Column(db.String(255), nullable=False)
    simulation_parameters_json = db.Column(db.Text, nullable=True)  # JSON stored as string
    status = db.Column(db.String(32), default='scheduled', nullable=False)  # scheduled, running, completed, aborted
    baseline_score = db.Column(db.Float, default=100.0, nullable=False)
    result_score = db.Column(db.Float, default=100.0, nullable=False)
    result_summary = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ChaosExperiment {self.name!r} target={self.target_service!r} status={self.status}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'experiment_type': self.experiment_type,
            'target_service': self.target_service,
            'hypothesis': self.hypothesis,
            'simulation_parameters_json': json.loads(self.simulation_parameters_json) if self.simulation_parameters_json else {},
            'status': self.status,
            'baseline_score': self.baseline_score,
            'result_score': self.result_score,
            'result_summary': self.result_summary,
            'organization_id': self.organization_id,
        }
