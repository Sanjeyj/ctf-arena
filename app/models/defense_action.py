import json
from app.extensions import db
from app.models.mixins import TimestampMixin

class DefenseAction(db.Model, TimestampMixin):
    """
    Simulated defensive response/SOC analyst action.
    """
    __tablename__ = 'defense_actions'

    id = db.Column(db.Integer, primary_key=True)
    
    # Links
    event_id = db.Column(db.Integer, db.ForeignKey('attack_events.id', ondelete='CASCADE'), nullable=False, index=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Analyst (User id or 'ai_blue_team')
    analyst = db.Column(db.String(80), nullable=False)
    
    # Action taken (e.g. isolate_host, block_ip, terminate_process)
    action = db.Column(db.String(120), nullable=False)
    
    # Performance metrics
    response_time = db.Column(db.Integer, nullable=True) # response delay in seconds
    effectiveness = db.Column(db.Float, default=1.0, nullable=False) # 0.0 to 1.0
    
    # Scoring
    points_awarded = db.Column(db.Float, default=0.0, nullable=False)

    _details = db.Column('details', db.Text, nullable=True)

    event = db.relationship('AttackEvent', back_populates='defense_actions')
    incident = db.relationship('Incident', back_populates='defense_actions')

    @property
    def details(self) -> dict:
        if self._details:
            try:
                return json.loads(self._details)
            except Exception:
                return {}
        return {}

    @details.setter
    def details(self, value: dict):
        self._details = json.dumps(value or {})

    def __repr__(self):
        return f'<DefenseAction action={self.action!r} analyst={self.analyst!r} effectiveness={self.effectiveness}>'
