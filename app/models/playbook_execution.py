"""
PlaybookExecution model - Phase 21 Playbook Engine.
Logs playbook runs and logs actions step by step.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class PlaybookExecution(db.Model, TimestampMixin, TenantMixin):
    """Playbook active and historical runs logging."""
    __tablename__ = 'playbook_executions'

    id = db.Column(db.Integer, primary_key=True)
    playbook_id = db.Column(db.Integer, db.ForeignKey('playbooks.id', ondelete='CASCADE'), nullable=False)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(32), default='pending') # pending, running, completed, failed
    current_step = db.Column(db.Integer, default=0)
    logs = db.Column(db.Text, default='')

    # Relationships
    playbook = db.relationship('Playbook', backref=db.backref('executions', cascade='all, delete-orphan', lazy='dynamic'))
    alert = db.relationship('Alert', backref=db.backref('playbook_executions', lazy='dynamic'))

    def __repr__(self):
        return f'<PlaybookExecution id={self.id} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'playbook_id': self.playbook_id,
            'alert_id': self.alert_id,
            'status': self.status,
            'current_step': self.current_step,
            'logs': self.logs,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None
        }
