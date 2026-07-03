"""
GovernanceFramework model - Phase 23 Governance & Compliance.
Details GRC frameworks (e.g. ISO 27001, NIST CSF, CIS Controls, MITRE ATT&CK).
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class GovernanceFramework(db.Model, TimestampMixin, TenantMixin):
    """Compliance framework config settings."""
    __tablename__ = 'governance_frameworks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True) # ISO27001, NIST-CSF, etc.
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<GovernanceFramework {self.name!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
