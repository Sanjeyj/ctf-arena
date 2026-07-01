from app.extensions import db
from app.models.hint import Hint, HintUnlock

class HintRepository:
    @staticmethod
    def get_by_id(hint_id):
        return Hint.query.get(hint_id)

    @staticmethod
    def get_for_challenge(challenge_id):
        return Hint.query.filter_by(challenge_id=challenge_id).order_by(Hint.display_order.asc(), Hint.id.asc()).all()

    @staticmethod
    def create(challenge_id, content, cost=0, title=None, visible=True, enabled=True, display_order=0):
        hint = Hint(
            challenge_id=challenge_id,
            content=content.strip(),
            cost=cost,
            title=title.strip() if title else None,
            visible=visible,
            enabled=enabled,
            display_order=display_order
        )
        db.session.add(hint)
        db.session.commit()
        return hint

    @staticmethod
    def update(hint, **kwargs):
        for k, v in kwargs.items():
            if hasattr(hint, k):
                if k == "content" and v is not None:
                    v = v.strip()
                elif k == "title" and v is not None:
                    v = v.strip()
                setattr(hint, k, v)
        db.session.commit()
        return hint

    @staticmethod
    def delete(hint):
        db.session.delete(hint)
        db.session.commit()

    @staticmethod
    def is_unlocked(hint_id, user_id):
        if not user_id:
            return False
        return HintUnlock.query.filter_by(user_id=user_id, hint_id=hint_id).first() is not None

    @staticmethod
    def unlock(hint_id, user_id):
        if not user_id:
            return False
        unlock = HintUnlock.query.filter_by(user_id=user_id, hint_id=hint_id).first()
        if not unlock:
            unlock = HintUnlock(user_id=user_id, hint_id=hint_id)
            db.session.add(unlock)
            db.session.commit()
            return True
        return False
