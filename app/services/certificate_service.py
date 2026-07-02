import datetime
import hashlib
import uuid
from app.extensions import db
from app.models.certificate import Certificate

class CertificateService:
    """Issue, verify, and revoke LMS completion certificates."""

    @staticmethod
    def issue(user_id: int, course_id: int = None, title: str = None,
              recipient_name: str = None, organization_id: int = None) -> Certificate:
        """
        Issue a new certificate. Always generates a unique verification_id and hash.
        state='issued' on creation.
        """
        verification_id = Certificate.generate_verification_id()
        raw = f"{user_id}:{course_id}:{verification_id}:{uuid.uuid4()}"
        cert_hash = hashlib.sha256(raw.encode()).hexdigest()

        cert = Certificate(
            user_id=user_id,
            course_id=course_id,
            title=title or 'Course Completion Certificate',
            recipient_name=recipient_name,
            organization_id=organization_id,
            verification_id=verification_id,
            hash=cert_hash,
            state='issued',
            issued_at=datetime.datetime.utcnow(),
        )
        db.session.add(cert)
        db.session.commit()
        return cert

    @staticmethod
    def verify(verification_id: str) -> tuple[Certificate | None, str]:
        """
        Verify a certificate by its verification_id.
        Returns (cert, None) on success or (None, error_message) on failure.
        """
        cert = Certificate.query.filter_by(verification_id=verification_id).first()
        if not cert:
            return None, 'Certificate not found.'
        if cert.state == 'revoked':
            return None, f'Certificate has been revoked: {cert.revoke_reason or "No reason provided."}'
        if cert.state == 'draft':
            return None, 'Certificate has not been issued yet.'
        return cert, None

    @staticmethod
    def revoke(cert: Certificate, reason: str = None) -> tuple[bool, str]:
        """Revoke an issued certificate."""
        if cert.state == 'revoked':
            return False, 'Certificate is already revoked.'
        cert.state = 'revoked'
        cert.revoked_at = datetime.datetime.utcnow()
        cert.revoke_reason = reason or 'Revoked by administrator.'
        db.session.commit()
        return True, None

    @staticmethod
    def get_user_certificates(user_id: int) -> list[Certificate]:
        return Certificate.query.filter_by(user_id=user_id, state='issued').all()
