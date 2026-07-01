from app.extensions import db, safe_commit
from app.models.flag import Flag

class FlagRepository:
    @staticmethod
    def get_by_id(flag_id):
        return Flag.query.get(flag_id)

    @staticmethod
    def get_for_challenge(challenge_id):
        return Flag.query.filter_by(challenge_id=challenge_id).order_by(Flag.priority.asc(), Flag.id.asc()).all()

    @staticmethod
    def create(challenge_id, content, flag_type="exact", is_case_sensitive=True, priority=0, notes=None, enabled=True):
        flag = Flag(
            challenge_id=challenge_id,
            content=content.strip(),
            flag_type=flag_type,
            is_case_sensitive=is_case_sensitive,
            priority=priority,
            notes=notes,
            enabled=enabled
        )
        db.session.add(flag)
        safe_commit()
        return flag

    @staticmethod
    def update(flag, **kwargs):
        for k, v in kwargs.items():
            if hasattr(flag, k):
                if k == "content" and v is not None:
                    v = v.strip()
                setattr(flag, k, v)
        safe_commit()
        return flag

    @staticmethod
    def delete(flag):
        db.session.delete(flag)
        safe_commit()
