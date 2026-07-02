import json
from app.extensions import db
from app.models.mixins import TimestampMixin

class AttackChain(db.Model, TimestampMixin):
    """
    Groups attack events into a chronological path/kill-chain progression.
    """
    __tablename__ = 'attack_chains'

    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(
        db.Integer, db.ForeignKey('attack_simulations.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    name = db.Column(db.String(120), nullable=False)
    
    # JSON list of technique IDs representing the expected path
    _expected_path = db.Column('expected_path', db.Text, nullable=True) # e.g. ["T1566", "T1059", "T1078"]
    
    # JSON list of actual event IDs linked
    _actual_events = db.Column('actual_events', db.Text, nullable=True) # e.g. [12, 13]

    completed = db.Column(db.Boolean, default=False, nullable=False)

    simulation = db.relationship('AttackSimulation', backref=db.backref('attack_chains', cascade='all, delete-orphan'))

    @property
    def expected_path(self) -> list:
        if self._expected_path:
            try:
                return json.loads(self._expected_path)
            except Exception:
                return []
        return []

    @expected_path.setter
    def expected_path(self, value: list):
        self._expected_path = json.dumps(value or [])

    @property
    def actual_events(self) -> list:
        if self._actual_events:
            try:
                return json.loads(self._actual_events)
            except Exception:
                return []
        return []

    @actual_events.setter
    def actual_events(self, value: list):
        self._actual_events = json.dumps(value or [])

    def __repr__(self):
        return f'<AttackChain {self.name!r} completed={self.completed}>'
