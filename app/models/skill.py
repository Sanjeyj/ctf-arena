from app.extensions import db
from app.models.mixins import TimestampMixin

SKILL_CATEGORIES = (
    'web_security', 'cryptography', 'reverse_engineering', 'forensics',
    'osint', 'cloud_security', 'incident_response', 'threat_hunting',
    'malware_analysis', 'red_team', 'blue_team',
)
MASTERY_LEVELS = ('novice', 'beginner', 'intermediate', 'advanced', 'expert')


class Skill(db.Model, TimestampMixin):
    """Definition of a tracked cybersecurity skill."""
    __tablename__ = 'lms_skills'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(40), nullable=False, index=True)
    icon = db.Column(db.String(10), default='🔐', nullable=False)

    user_skills = db.relationship('UserSkill', back_populates='skill', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Skill {self.slug!r}>'


class UserSkill(db.Model, TimestampMixin):
    """Tracks XP and mastery level a user has in a specific Skill."""
    __tablename__ = 'lms_user_skills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('lms_skills.id', ondelete='CASCADE'), nullable=False, index=True)

    xp = db.Column(db.Integer, default=0, nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)        # 1–10 numeric level
    mastery = db.Column(db.String(20), default='novice', nullable=False)  # One of MASTERY_LEVELS

    __table_args__ = (
        db.UniqueConstraint('user_id', 'skill_id', name='uq_user_skill'),
    )

    skill = db.relationship('Skill', back_populates='user_skills')

    def __repr__(self):
        return f'<UserSkill user={self.user_id} skill={self.skill_id} xp={self.xp}>'
