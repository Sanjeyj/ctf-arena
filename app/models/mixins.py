import uuid
import datetime
from app.extensions import db, utcnow

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

class UUIDMixin:
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)

class SoftDeleteMixin:
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)

    def soft_delete(self):
        self.is_deleted = True


class TenantMixin:
    """
    Additive mixin that gives a model an organization_id column.

    Tenant isolation is enforced at the **service layer** only.
    No SQLAlchemy session hooks, no event listeners.

    Usage in a service::

        challenges = TenantMixin.tenant_filter(
            Challenge.query, org_id=g.current_org.id
        ).all()
    """
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey('organizations.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )

    @classmethod
    def tenant_filter(cls, query, org_id):
        """Filter a query to only return records belonging to org_id."""
        return query.filter(cls.organization_id == org_id)

    @classmethod
    def tenant_or_null(cls, query, org_id):
        """Filter a query to org_id OR records with NULL (default/legacy data)."""
        return query.filter(
            db.or_(cls.organization_id == org_id, cls.organization_id.is_(None))
        )
