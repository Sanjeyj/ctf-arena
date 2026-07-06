"""
DefenseDomain model - Phase 30 Unified Cyber Defense Universe.
Represents logical security domains inside a universe.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DefenseDomain(db.Model, TimestampMixin, TenantMixin):
    """Defense domain model."""
    __tablename__ = 'defense_domains'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('defense_universes.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    domain_type = db.Column(db.String(64), nullable=False)  # soc, cti, cyber_range, lms, grc, cloud, resilience, command, intelligence, unknown
    health_score = db.Column(db.Float, default=1.0, nullable=False)
    readiness_score = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(32), default='healthy', nullable=False)

    def __repr__(self):
        return f'<DefenseDomain {self.name!r} type={self.domain_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'universe_id': self.universe_id,
            'name': self.name,
            'domain_type': self.domain_type,
            'health_score': self.health_score,
            'readiness_score': self.readiness_score,
            'status': self.status,
            'organization_id': self.organization_id,
        }
