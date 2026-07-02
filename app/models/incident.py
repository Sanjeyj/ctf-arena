from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

INCIDENT_STATUSES = ('open', 'investigating', 'contained', 'resolved')
INCIDENT_WORKFLOW_STAGES = ('detection', 'analysis', 'containment', 'eradication', 'recovery', 'lessons_learned')


class Incident(db.Model, TimestampMixin, UUIDMixin):
    """
    Simulated security incident created from one or more attack events.
    Tracks workflow lifecycle for Blue Team exercises.
    """
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)

    simulation_id = db.Column(
        db.Integer, db.ForeignKey('attack_simulations.id', ondelete='CASCADE'),
        nullable=False, index=True
    )

    status = db.Column(db.String(20), default='open', nullable=False, index=True)
    workflow_stage = db.Column(db.String(30), default='detection', nullable=False, index=True)

    assigned_to = db.Column(db.String(80), nullable=True)  # Analyst identifier

    # Timestamps
    detected_at = db.Column(db.DateTime, nullable=True)
    contained_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    simulation = db.relationship('AttackSimulation', back_populates='incidents')
    defense_actions = db.relationship('DefenseAction', back_populates='incident')

    def __repr__(self):
        return f'<Incident {self.title!r} status={self.status} workflow={self.workflow_stage}>'
