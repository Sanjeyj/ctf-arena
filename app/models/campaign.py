"""
Campaign model - Phase 19 Security Research & CTI Platform.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class Campaign(db.Model, TimestampMixin, TenantMixin):
    """Cyber threat actor active campaign details."""
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('threat_actors.id', ondelete='CASCADE'), nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    target_sector = db.Column(db.String(120), nullable=True) # e.g. Finance, Healthcare
    description = db.Column(db.Text, nullable=True)
    
    # Associated malware families / ATT&CK techniques used (comma-separated tags / list representation in service layer)
    malware_used = db.Column(db.Text, nullable=True) # comma-separated list
    techniques_used = db.Column(db.Text, nullable=True) # comma-separated list

    def __repr__(self):
        return f'<Campaign {self.name!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'actor_id': self.actor_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'target_sector': self.target_sector,
            'description': self.description,
            'malware_used': [m.strip() for m in self.malware_used.split(',')] if self.malware_used else [],
            'techniques_used': [t.strip() for t in self.techniques_used.split(',')] if self.techniques_used else [],
            'organization_id': self.organization_id
        }
