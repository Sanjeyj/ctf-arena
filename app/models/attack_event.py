import json
from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

ATTACK_TACTICS = (
    'initial_access', 'execution', 'persistence', 'privilege_escalation',
    'defense_evasion', 'credential_access', 'discovery', 'lateral_movement',
    'collection', 'exfiltration', 'impact',
)

SEVERITY_LEVELS = ('info', 'low', 'medium', 'high', 'critical')


class AttackEvent(db.Model, TimestampMixin, UUIDMixin):
    """
    A single simulated attack action within a simulation.
    Maps to a MITRE ATT&CK tactic + technique.
    """
    __tablename__ = 'attack_events'

    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(
        db.Integer, db.ForeignKey('attack_simulations.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    # Optional link to a MITRE technique
    mitre_technique_id = db.Column(
        db.Integer, db.ForeignKey('mitre_techniques.id', ondelete='SET NULL'),
        nullable=True, index=True
    )

    tactic = db.Column(db.String(40), nullable=False, index=True)
    technique = db.Column(db.String(100), nullable=True)
    technique_id = db.Column(db.String(20), nullable=True)  # e.g. T1566, T1059


    severity = db.Column(db.String(20), default='medium', nullable=False, index=True)
    source = db.Column(db.String(120), nullable=True)   # attacking host/IP (simulated)
    target = db.Column(db.String(120), nullable=True)   # target host (simulated)

    detected = db.Column(db.Boolean, default=False, nullable=False)
    detected_at = db.Column(db.DateTime, nullable=True)

    # Optional payload metadata (never real exploits; structured description only)
    _payload_metadata = db.Column('payload_metadata', db.Text, nullable=True)

    # Scoring
    points_awarded = db.Column(db.Float, default=0.0, nullable=False)

    simulation = db.relationship('AttackSimulation', back_populates='events')
    mitre_technique = db.relationship('MitreTechnique', backref='events')
    defense_actions = db.relationship('DefenseAction', back_populates='event', cascade='all, delete-orphan')

    @property
    def payload_metadata(self) -> dict:
        if self._payload_metadata:
            try:
                return json.loads(self._payload_metadata)
            except Exception:
                return {}
        return {}

    @payload_metadata.setter
    def payload_metadata(self, value: dict):
        self._payload_metadata = json.dumps(value or {})


    def __repr__(self):
        return f'<AttackEvent [{self.tactic}] {self.technique!r} sev={self.severity}>'
