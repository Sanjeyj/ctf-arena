"""Phase 40 — Architecture Decision Record (ADR) Model."""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ArchitectureDecisionRecord(db.Model, TimestampMixin, TenantMixin):
    """Structured record of an architecture decision with full FSM lifecycle."""
    __tablename__ = 'architecture_decision_records'

    STATUS_CHOICES = ('proposed', 'accepted', 'deprecated', 'superseded')

    # Valid state transitions
    VALID_TRANSITIONS = {
        'proposed': ('accepted', 'deprecated'),
        'accepted': ('deprecated', 'superseded'),
        'deprecated': ('superseded',),
        'superseded': (),
    }

    id = db.Column(db.Integer, primary_key=True)
    adr_key = db.Column(db.String(60), nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)
    context = db.Column(db.Text, nullable=True)
    decision = db.Column(db.Text, nullable=False)
    consequences = db.Column(db.Text, nullable=True)
    alternatives_json = db.Column(db.Text, nullable=True)
    affected_modules_json = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='proposed', index=True)
    approved_by = db.Column(db.String(120), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('adr_key', 'organization_id', name='uq_adr_key_org'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'adr_key': self.adr_key,
            'title': self.title,
            'context': self.context,
            'decision': self.decision,
            'consequences': self.consequences,
            'alternatives_json': self.alternatives_json,
            'affected_modules_json': self.affected_modules_json,
            'status': self.status,
            'approved_by': self.approved_by,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
