from app.extensions import db, safe_commit
from app.models.competition import Competition
import datetime

class CompetitionRepository:
    @staticmethod
    def get_all():
        return Competition.query.all()

    @staticmethod
    def get_by_id(comp_id):
        return Competition.query.get(comp_id)

    @staticmethod
    def get_by_name(name):
        return Competition.query.filter_by(name=name).first()

    @staticmethod
    def get_active():
        # Get first active (non-archived) competition
        return Competition.query.filter_by(is_active=True, is_archived=False).first()

    @staticmethod
    def create(name, description=None, start_time=None, end_time=None,
               registration_open=None, registration_close=None,
               freeze_time=None, unfreeze_time=None, is_active=True,
               is_paused=False, is_archived=False, visibility="public",
               allow_practice=True, max_attempts=0, rules=None, banner=None, created_by=None):
        comp = Competition(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            registration_open=registration_open,
            registration_close=registration_close,
            freeze_time=freeze_time,
            unfreeze_time=unfreeze_time,
            is_active=is_active,
            is_paused=is_paused,
            is_archived=is_archived,
            visibility=visibility,
            allow_practice=allow_practice,
            max_attempts=max_attempts,
            rules=rules,
            banner=banner,
            created_by=created_by
        )
        db.session.add(comp)
        safe_commit()
        return comp

    @staticmethod
    def update(comp_id, **kwargs):
        comp = Competition.query.get(comp_id)
        if comp:
            for k, v in kwargs.items():
                if hasattr(comp, k):
                    setattr(comp, k, v)
            safe_commit()
        return comp

    @staticmethod
    def delete(comp_id):
        comp = Competition.query.get(comp_id)
        if comp:
            db.session.delete(comp)
            safe_commit()
            return True
        return False
