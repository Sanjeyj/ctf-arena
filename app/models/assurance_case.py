"""
AssuranceCase model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Structured claims and assurance cases.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class AssuranceCase(db.Model, TimestampMixin, TenantMixin):
    """AssuranceCase model."""
    __tablename__ = 'assurance_cases'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    claim = db.Column(db.Text, nullable=False)
    scope = db.Column(db.String(120), nullable=True)
    confidence_score = db.Column(db.Float, default=0.0, nullable=False)  # 0 to 100
    status = db.Column(db.String(64), default='draft', nullable=False, index=True)  # draft, under_review, supported, insufficient_evidence, retired
    owner = db.Column(db.String(120), nullable=True)
    version = db.Column(db.String(32), default='1.0.0', nullable=False)

    def __repr__(self):
        return f'<AssuranceCase {self.title!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'claim': self.claim,
            'scope': self.scope,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'owner': self.owner,
            'version': self.version,
            'organization_id': self.organization_id,
        }
