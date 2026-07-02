from app.extensions import db
from app.models.badge import Badge, UserBadge

# Badge catalog seeded on first use
BADGE_CATALOG = [
    {'slug': 'first_blood',       'name': 'First Blood',       'icon': '🩸', 'color': '#ff3366', 'category': 'achievement', 'xp_value': 100, 'description': 'First to solve a challenge.'},
    {'slug': '100_points',        'name': '100 Points',        'icon': '💯', 'color': '#ffd700', 'category': 'achievement', 'xp_value': 50,  'description': 'Earned 100 total points.'},
    {'slug': '500_points',        'name': '500 Points',        'icon': '⭐', 'color': '#ffd700', 'category': 'achievement', 'xp_value': 150, 'description': 'Earned 500 total points.'},
    {'slug': '10_challenges',     'name': '10 Challenges',     'icon': '🔟', 'color': '#00f0ff', 'category': 'achievement', 'xp_value': 100, 'description': 'Completed 10 challenges.'},
    {'slug': 'soc_analyst',       'name': 'SOC Analyst',       'icon': '🛡️', 'color': '#00ff66', 'category': 'skill',       'xp_value': 200, 'description': 'Completed the SOC Analyst learning path.'},
    {'slug': 'red_teamer',        'name': 'Red Teamer',        'icon': '⚔️', 'color': '#ff3366', 'category': 'skill',       'xp_value': 200, 'description': 'Completed the Red Team learning path.'},
    {'slug': 'cyber_ranger',      'name': 'Cyber Ranger',      'icon': '🎯', 'color': '#bf5af2', 'category': 'range',       'xp_value': 250, 'description': 'Completed a full Cyber Range simulation.'},
    {'slug': 'course_graduate',   'name': 'Course Graduate',   'icon': '🎓', 'color': '#00f0ff', 'category': 'course',      'xp_value': 100, 'description': 'Completed an LMS course.'},
]


class BadgeService:
    @staticmethod
    def seed_badges():
        """Populate the badge catalog if empty."""
        if Badge.query.first():
            return
        for item in BADGE_CATALOG:
            b = Badge(**item)
            db.session.add(b)
        db.session.commit()

    @staticmethod
    def get_badge(slug: str) -> Badge:
        BadgeService.seed_badges()
        return Badge.query.filter_by(slug=slug).first()

    @staticmethod
    def award(user_id: int, badge_slug: str, awarded_by: str = 'system', reason: str = None) -> tuple[UserBadge | None, str]:
        """Award a badge to a user. Idempotent — returns existing if already awarded."""
        badge = BadgeService.get_badge(badge_slug)
        if not badge:
            return None, f'Badge {badge_slug!r} not found in catalog.'

        existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
        if existing:
            return existing, None  # Already awarded — idempotent

        ub = UserBadge(user_id=user_id, badge_id=badge.id, awarded_by=awarded_by, reason=reason)
        db.session.add(ub)
        db.session.commit()
        return ub, None

    @staticmethod
    def get_user_badges(user_id: int) -> list[UserBadge]:
        return UserBadge.query.filter_by(user_id=user_id).all()

    @staticmethod
    def has_badge(user_id: int, badge_slug: str) -> bool:
        badge = BadgeService.get_badge(badge_slug)
        if not badge:
            return False
        return UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).count() > 0
