import json
from app.extensions import db
from app.models.mixins import TimestampMixin

class CourseProgress(db.Model, TimestampMixin):
    """Tracks a student's detailed progress within a course enrollment."""
    __tablename__ = 'lms_progress'

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('lms_enrollments.id', ondelete='CASCADE'), nullable=False, unique=True)

    percentage = db.Column(db.Float, default=0.0, nullable=False)  # 0.0–100.0

    # JSON lists of completed lesson/module IDs
    _completed_lessons = db.Column('completed_lessons', db.Text, nullable=True)
    _completed_modules = db.Column('completed_modules', db.Text, nullable=True)

    enrollment = db.relationship('CourseEnrollment', back_populates='progress')

    @property
    def completed_lessons(self) -> list:
        if self._completed_lessons:
            try:
                return json.loads(self._completed_lessons)
            except Exception:
                return []
        return []

    @completed_lessons.setter
    def completed_lessons(self, value: list):
        self._completed_lessons = json.dumps(list(set(value or [])))

    @property
    def completed_modules(self) -> list:
        if self._completed_modules:
            try:
                return json.loads(self._completed_modules)
            except Exception:
                return []
        return []

    @completed_modules.setter
    def completed_modules(self, value: list):
        self._completed_modules = json.dumps(list(set(value or [])))

    def mark_lesson_complete(self, lesson_id: int):
        current = self.completed_lessons
        if lesson_id not in current:
            current.append(lesson_id)
            self.completed_lessons = current

    def __repr__(self):
        return f'<CourseProgress enrollment={self.enrollment_id} pct={self.percentage:.1f}%>'
