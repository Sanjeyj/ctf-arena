import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin

ENROLLMENT_STATUSES = ('active', 'completed', 'dropped', 'expired')

class CourseEnrollment(db.Model, TimestampMixin):
    """Tracks a student's enrollment in a Course."""
    __tablename__ = 'lms_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('lms_courses.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), default='active', nullable=False, index=True)
    enrolled_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='uq_enrollment_user_course'),
    )

    course = db.relationship('Course', back_populates='enrollments')
    progress = db.relationship('CourseProgress', back_populates='enrollment', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CourseEnrollment user={self.user_id} course={self.course_id} status={self.status}>'
