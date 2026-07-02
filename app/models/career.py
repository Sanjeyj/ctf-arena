import json
from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Job(db.Model, TimestampMixin, UUIDMixin):
    """A job posting linked to the career platform."""
    __tablename__ = 'career_jobs'

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('career_employers.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    remote = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    _required_skills = db.Column('required_skills', db.Text, nullable=True)  # JSON list of skill slugs
    _required_badges = db.Column('required_badges', db.Text, nullable=True)  # JSON list of badge slugs

    employer = db.relationship('Employer', back_populates='jobs')

    @property
    def required_skills(self) -> list:
        try:
            return json.loads(self._required_skills or '[]')
        except Exception:
            return []

    @required_skills.setter
    def required_skills(self, value: list):
        self._required_skills = json.dumps(value or [])

    @property
    def required_badges(self) -> list:
        try:
            return json.loads(self._required_badges or '[]')
        except Exception:
            return []

    @required_badges.setter
    def required_badges(self, value: list):
        self._required_badges = json.dumps(value or [])

    def __repr__(self):
        return f'<Job {self.title!r}>'


class Employer(db.Model, TimestampMixin, UUIDMixin):
    """Company/organization that lists job postings on the career platform."""
    __tablename__ = 'career_employers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    jobs = db.relationship('Job', back_populates='employer', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Employer {self.name!r}>'


class Resume(db.Model, TimestampMixin, UUIDMixin):
    """Auto-generated resume profile for a user based on skills, badges, and certs."""
    __tablename__ = 'career_resumes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    headline = db.Column(db.String(160), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    public = db.Column(db.Boolean, default=False, nullable=False)
    share_url = db.Column(db.String(80), unique=True, nullable=True)   # UUID-based public URL

    def __repr__(self):
        return f'<Resume user={self.user_id}>'
