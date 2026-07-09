"""
FederationGovernanceRecord model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Records federated governance proposals and decisions about collective cyber risk
posture. Human approval is mandatory for state transitions from 'reviewing' to
'approved' or 'rejected'.
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class FederationGovernanceRecord(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'federation_governance_records'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    decision_type = db.Column(db.String(64), nullable=False)
    # collective_control, dependency_diversification, shared_recovery,
    # mutual_aid_policy, sector_priority, systemic_risk_acceptance,
    # collective_investment
    scope = db.Column(db.String(120), nullable=True)
    proposal_summary = db.Column(db.Text, nullable=True)
    participating_entities_json = db.Column(db.Text, default='[]')
    support_score = db.Column(db.Float, default=0.0)               # 0-100
    opposition_score = db.Column(db.Float, default=0.0)            # 0-100
    consensus_score = db.Column(db.Float, default=0.0)             # 0-100
    systemic_risk_impact = db.Column(db.Float, default=0.0)        # -100 to +100 (negative = risk reduction)
    collective_resilience_impact = db.Column(db.Float, default=0.0)# 0-100
    decision_status = db.Column(db.String(32), default='proposed')
    # proposed, reviewing, approved, rejected, deferred, superseded
    approved_by = db.Column(db.String(120), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.Index('ix_federation_gov_org', 'organization_id'),
        db.Index('ix_federation_gov_decided_at', 'decided_at'),
    )

    def __repr__(self):
        return f'<FederationGovernanceRecord {self.title!r} status={self.decision_status}>'

    def to_dict(self):
        import json
        try:
            entities = json.loads(self.participating_entities_json or '[]')
        except Exception:
            entities = []
        return {
            'id': self.id,
            'title': self.title,
            'decision_type': self.decision_type,
            'scope': self.scope,
            'proposal_summary': self.proposal_summary,
            'participating_entities': entities,
            'support_score': self.support_score,
            'opposition_score': self.opposition_score,
            'consensus_score': self.consensus_score,
            'systemic_risk_impact': self.systemic_risk_impact,
            'collective_resilience_impact': self.collective_resilience_impact,
            'decision_status': self.decision_status,
            'approved_by': self.approved_by,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
            'organization_id': self.organization_id,
        }
