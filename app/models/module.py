from app.extensions import db
from app.models.mixins import TimestampMixin

class CourseModule(db.Model, TimestampMixin):
    """An ordered section within a Course containing lessons."""
    __tablename__ = 'lms_modules'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('lms_courses.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0, nullable=False)

    course = db.relationship('Course', back_populates='modules')
    lessons = db.relationship('Lesson', back_populates='module', cascade='all, delete-orphan', order_by='Lesson.order')

    def __repr__(self):
        return f'<CourseModule {self.title!r} course_id={self.course_id}>'
