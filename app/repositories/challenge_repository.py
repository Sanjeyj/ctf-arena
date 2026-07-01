from app.extensions import db
from app.models.challenge import Challenge

class ChallengeRepository:
    @staticmethod
    def get_by_id(ch_id):
        return Challenge.query.filter_by(id=ch_id, is_deleted=False).first()

    @staticmethod
    def get_by_legacy_id(legacy_id):
        return Challenge.query.filter_by(legacy_id=legacy_id, is_deleted=False).first()

    @staticmethod
    def get_all(include_hidden=True):
        q = Challenge.query.filter_by(is_deleted=False)
        if not include_hidden:
            q = q.filter_by(visible=True, state="visible")
        return q.order_by(Challenge.display_order.asc(), Challenge.id.asc()).all()

    @staticmethod
    def create(legacy_id, title, description, points, difficulty, category_id=None, **kwargs):
        ch = Challenge(
            legacy_id=legacy_id.strip(),
            title=title.strip(),
            description=description.strip(),
            points=points,
            difficulty=difficulty,
            category_id=category_id,
            initial_points=kwargs.get("initial_points", points),
            minimum_points=kwargs.get("minimum_points", points),
            current_points=kwargs.get("current_points", points),
            decay_type=kwargs.get("decay_type", "static"),
            decay_rate=kwargs.get("decay_rate", 0),
            max_attempts=kwargs.get("max_attempts", 0),
            requires_connection_info=kwargs.get("requires_connection_info", False),
            connection_info=kwargs.get("connection_info"),
            visible=kwargs.get("visible", True),
            state=kwargs.get("state", "visible"),
            display_order=kwargs.get("display_order", 0),
            featured=kwargs.get("featured", False),
            archived=kwargs.get("archived", False)
        )
        for k, v in kwargs.items():
            if hasattr(ch, k) and k not in ["initial_points", "minimum_points", "current_points", "decay_type", "decay_rate", "max_attempts", "requires_connection_info", "connection_info", "visible", "state", "display_order", "featured", "archived"]:
                setattr(ch, k, v)
        db.session.add(ch)
        db.session.commit()
        return ch

    @staticmethod
    def update(challenge, **kwargs):
        for k, v in kwargs.items():
            if hasattr(challenge, k):
                if isinstance(v, str):
                    v = v.strip()
                setattr(challenge, k, v)
        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        # Perform soft delete using the mixin property
        challenge.is_deleted = True
        db.session.commit()

    @staticmethod
    def list_challenges(search=None, category_id=None, difficulty=None, visibility=None, state=None, author_id=None, sort_by=None, page=None, per_page=None):
        q = Challenge.query.filter_by(is_deleted=False)

        if search:
            search_pattern = f"%{search.strip()}%"
            q = q.filter(Challenge.title.like(search_pattern) | Challenge.description.like(search_pattern) | Challenge.legacy_id.like(search_pattern))

        if category_id:
            q = q.filter_by(category_id=category_id)

        if difficulty:
            q = q.filter_by(difficulty=difficulty)

        if visibility is not None:
            q = q.filter_by(visible=visibility)

        if state:
            q = q.filter_by(state=state)

        if author_id:
            q = q.filter_by(author_id=author_id)

        # Sorting logic
        if sort_by == "newest":
            q = q.order_by(Challenge.published_at.desc(), Challenge.id.desc())
        elif sort_by == "oldest":
            q = q.order_by(Challenge.published_at.asc(), Challenge.id.asc())
        elif sort_by == "title":
            q = q.order_by(Challenge.title.asc())
        elif sort_by == "points":
            q = q.order_by(Challenge.current_points.desc(), Challenge.id.desc())
        elif sort_by == "difficulty":
            q = q.order_by(Challenge.difficulty.asc(), Challenge.id.asc())
        elif sort_by == "solves":
            q = q.order_by(Challenge.solve_count.desc(), Challenge.id.desc())
        else: # Default display order
            q = q.order_by(Challenge.display_order.asc(), Challenge.id.asc())

        if page and per_page:
            return q.paginate(page=page, per_page=per_page, error_out=False)
        return q.all()
