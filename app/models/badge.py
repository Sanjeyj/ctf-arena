from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

BADGE_CATEGORIES = ('achievement', 'skill', 'course', 'community', 'range')

class Badge(db.Model, TimestampMixin, UUIDMixin):
    """Gamification badge awarded for milestones and achievements."""
    __tablename__ = 'lms_badges'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), default='🏅', nullable=False)       # Emoji or icon key
    color = db.Column(db.String(10), default='#ffd700', nullable=False)
    category = db.Column(db.String(20), default='achievement', nullable=False, index=True)
    xp_value = db.Column(db.Integer, default=50, nullable=False)

    awards = db.relationship('UserBadge', back_populates='badge', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Badge {self.slug!r}>'


class UserBadge(db.Model, TimestampMixin):
    """Association table linking a Badge award to a specific user."""
    __tablename__ = 'lms_user_badges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('lms_badges.id', ondelete='CASCADE'), nullable=False, index=True)
    awarded_by = db.Column(db.String(80), nullable=True)   # Admin username or 'system'
    reason = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )

    badge = db.relationship('Badge', back_populates='awards')

    def __repr__(self):
        return f'<UserBadge user={self.user_id} badge={self.badge_id}>'
