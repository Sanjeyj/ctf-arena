from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

SIMULATION_STATUSES = ('pending', 'running', 'paused', 'completed', 'aborted')
ATTACKER_TYPES = ('easy_ai', 'medium_ai', 'hard_ai', 'adaptive_ai', 'manual')
DEFENDER_TYPES = ('l1_soc', 'l2_soc', 'l3_soc', 'ai_blue_team', 'manual')


class AttackSimulation(db.Model, TimestampMixin, UUIDMixin):
    """
    Represents a complete cyber range simulation session.
    Contains one AI attacker versus one AI/human defender.
    """
    __tablename__ = 'attack_simulations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Multi-tenant support
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)

    # Participants
    attacker_type = db.Column(db.String(30), default='easy_ai', nullable=False)
    defender_type = db.Column(db.String(30), default='l1_soc', nullable=False)

    # Status lifecycle: pending → running → completed / aborted
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)

    # Timing
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)

    # Scoring
    red_score = db.Column(db.Float, default=0.0, nullable=False)
    blue_score = db.Column(db.Float, default=0.0, nullable=False)

    # Relationships
    events = db.relationship('AttackEvent', back_populates='simulation', cascade='all, delete-orphan', lazy='dynamic')
    incidents = db.relationship('Incident', back_populates='simulation', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<AttackSimulation {self.name!r} status={self.status}>'
