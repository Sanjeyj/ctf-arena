import uuid
import datetime
from app.extensions import db

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

class UUIDMixin:
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)

class SoftDeleteMixin:
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)

    def soft_delete(self):
        self.is_deleted = True
