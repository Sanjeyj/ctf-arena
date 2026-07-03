"""
Policy model - Phase 23 Enterprise Governance.
Stores security policies draft and approval workflows.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class Policy(db.Model, TimestampMixin, TenantMixin):
    """Corporate cybersecurity policy."""
    __tablename__ = 'policies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True, index=True)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(32), default='draft') # draft, approved
    expiration_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Policy {self.title!r} version={self.version}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'version': self.version,
            'status': self.status,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None
        }
