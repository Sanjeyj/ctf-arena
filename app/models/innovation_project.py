"""
InnovationProject model - Phase 28 Cyber Civilization Platform.
Tracks R&D security innovation projects.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class InnovationProject(db.Model, TimestampMixin, TenantMixin):
    """Innovation project model."""
    __tablename__ = 'innovation_projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), nullable=False)  # AI, Crypto, OS, Network, Hardware
    progress = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 to 1.0
    owner = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<InnovationProject {self.title!r} progress={self.progress}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'progress': self.progress,
            'owner': self.owner,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
