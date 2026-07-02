import json
from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

LEARNING_PATHS = {
    'beginner_analyst': {
        'name': 'Beginner Analyst',
        'description': 'Start your cybersecurity journey with foundational concepts.',
        'skills': ['web_security', 'forensics', 'osint'],
        'color': '#00f0ff',
    },
    'soc_analyst': {
        'name': 'SOC Analyst',
        'description': 'Master security operations center workflows and incident triage.',
        'skills': ['incident_response', 'threat_hunting', 'forensics'],
        'color': '#00ff66',
    },
    'pentester': {
        'name': 'Pentester',
        'description': 'Develop offensive security skills across web, network, and systems.',
        'skills': ['web_security', 'reverse_engineering', 'cryptography'],
        'color': '#ff3366',
    },
    'bug_hunter': {
        'name': 'Bug Hunter',
        'description': 'Find and responsibly disclose software vulnerabilities.',
        'skills': ['web_security', 'osint', 'reverse_engineering'],
        'color': '#ffd700',
    },
    'cloud_security': {
        'name': 'Cloud Security',
        'description': 'Secure cloud-native infrastructure and DevSecOps pipelines.',
        'skills': ['cloud_security', 'incident_response'],
        'color': '#bf5af2',
    },
    'malware_analyst': {
        'name': 'Malware Analyst',
        'description': 'Analyze and dissect malicious code and threat actor TTPs.',
        'skills': ['reverse_engineering', 'malware_analysis', 'forensics'],
        'color': '#ff9500',
    },
    'red_team': {
        'name': 'Red Team',
        'description': 'Advanced adversarial simulation and attack coordination.',
        'skills': ['red_team', 'web_security', 'reverse_engineering'],
        'color': '#ff3366',
    },
    'blue_team': {
        'name': 'Blue Team',
        'description': 'Defensive operations, detection engineering, and threat hunting.',
        'skills': ['blue_team', 'incident_response', 'threat_hunting'],
        'color': '#00f0ff',
    },
}


class LearningPath(db.Model, TimestampMixin, UUIDMixin):
    """A curated learning path tracking skill progression towards a career goal."""
    __tablename__ = 'lms_learning_paths'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(10), default='#00f0ff', nullable=False)
    _required_skills = db.Column('required_skills', db.Text, nullable=True)  # JSON list of skill slugs

    enrollments = db.relationship('PathEnrollment', back_populates='path', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def required_skills(self) -> list:
        if self._required_skills:
            try:
                return json.loads(self._required_skills)
            except Exception:
                return []
        return []

    @required_skills.setter
    def required_skills(self, value: list):
        self._required_skills = json.dumps(value or [])

    def __repr__(self):
        return f'<LearningPath {self.slug!r}>'


class PathEnrollment(db.Model, TimestampMixin):
    """Tracks a user enrolled in a LearningPath."""
    __tablename__ = 'lms_path_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    path_id = db.Column(db.Integer, db.ForeignKey('lms_learning_paths.id', ondelete='CASCADE'), nullable=False, index=True)
    progress_pct = db.Column(db.Float, default=0.0, nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'path_id', name='uq_path_enrollment'),
    )

    path = db.relationship('LearningPath', back_populates='enrollments')

    def __repr__(self):
        return f'<PathEnrollment user={self.user_id} path={self.path_id} pct={self.progress_pct}%>'
