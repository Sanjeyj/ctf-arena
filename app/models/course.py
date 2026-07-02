import json
from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

COURSE_DIFFICULTIES = ('beginner', 'intermediate', 'advanced', 'expert')
COURSE_CATEGORIES = (
    'web_security', 'cryptography', 'reverse_engineering', 'forensics',
    'osint', 'cloud_security', 'incident_response', 'threat_hunting',
    'malware_analysis', 'red_team', 'blue_team', 'general',
)

class Course(db.Model, TimestampMixin, UUIDMixin):
    """An LMS course containing ordered modules and lessons."""
    __tablename__ = 'lms_courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), default='beginner', nullable=False, index=True)
    category = db.Column(db.String(40), default='general', nullable=False, index=True)
    estimated_hours = db.Column(db.Float, default=1.0, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    thumbnail_url = db.Column(db.String(255), nullable=True)

    # Authored by
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Multi-tenant
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)

    modules = db.relationship('CourseModule', back_populates='course', cascade='all, delete-orphan', order_by='CourseModule.order')
    enrollments = db.relationship('CourseEnrollment', back_populates='course', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def total_lessons(self):
        count = 0
        for m in self.modules:
            count += len(m.lessons)
        return count

    def __repr__(self):
        return f'<Course {self.title!r} diff={self.difficulty}>'
