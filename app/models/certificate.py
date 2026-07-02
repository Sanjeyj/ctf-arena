import uuid
import hashlib
from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

CERT_STATES = ('draft', 'issued', 'revoked')

class Certificate(db.Model, TimestampMixin, UUIDMixin):
    """LMS completion certificate with verification ID and QR support."""
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    # Legacy challenge cert FK (kept for backwards compat, nullable)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='SET NULL'), nullable=True, index=True)
    hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Phase 17: LMS fields
    course_id = db.Column(db.Integer, db.ForeignKey('lms_courses.id', ondelete='SET NULL'), nullable=True, index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)

    verification_id = db.Column(db.String(32), unique=True, nullable=True, index=True)
    state = db.Column(db.String(10), default='issued', nullable=False, index=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoke_reason = db.Column(db.String(255), nullable=True)

    # Descriptive fields for the certificate face
    title = db.Column(db.String(200), nullable=True)         # e.g. "Web Security Fundamentals"
    recipient_name = db.Column(db.String(120), nullable=True)

    @staticmethod
    def generate_verification_id() -> str:
        return uuid.uuid4().hex[:24].upper()

    def __repr__(self):
        return f'<Certificate user={self.user_id} state={self.state} vid={self.verification_id}>'
