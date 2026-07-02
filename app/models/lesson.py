import json
from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Lesson(db.Model, TimestampMixin, UUIDMixin):
    """A single learning unit inside a CourseModule."""
    __tablename__ = 'lms_lessons'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('lms_modules.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    content_md = db.Column(db.Text, nullable=True)         # Markdown content
    video_url = db.Column(db.String(255), nullable=True)   # Embedded video URL
    order = db.Column(db.Integer, default=0, nullable=False)

    # Lab integration flags
    lab_required = db.Column(db.Boolean, default=False, nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete='SET NULL'), nullable=True)
    simulation_required = db.Column(db.Boolean, default=False, nullable=False)

    # Duration in minutes
    duration_minutes = db.Column(db.Integer, default=15, nullable=False)

    _attachments = db.Column('attachments', db.Text, nullable=True)  # JSON list of filenames

    module = db.relationship('CourseModule', back_populates='lessons')

    @property
    def attachments(self) -> list:
        if self._attachments:
            try:
                return json.loads(self._attachments)
            except Exception:
                return []
        return []

    @attachments.setter
    def attachments(self, value: list):
        self._attachments = json.dumps(value or [])

    def __repr__(self):
        return f'<Lesson {self.title!r} module_id={self.module_id}>'
