"""
ThreatActor model - Phase 19 Security Research & CTI Platform.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ThreatActor(db.Model, TimestampMixin, TenantMixin):
    """Threat Actor profile intelligence details."""
    __tablename__ = 'threat_actors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    aliases = db.Column(db.Text, nullable=True) # comma-separated list
    country = db.Column(db.String(80), nullable=True)
    motivation = db.Column(db.String(120), nullable=True)
    sophistication = db.Column(db.String(80), nullable=True) # e.g. state-sponsored, novice

    # Relationships
    campaigns = db.relationship('Campaign', backref='threat_actor', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<ThreatActor {self.name!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'aliases': [a.strip() for a in self.aliases.split(',')] if self.aliases else [],
            'country': self.country,
            'motivation': self.motivation,
            'sophistication': self.sophistication,
            'organization_id': self.organization_id
        }
