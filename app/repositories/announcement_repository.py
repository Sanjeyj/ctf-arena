from app.extensions import db, safe_commit
from app.models.announcement import Announcement
import datetime

class AnnouncementRepository:
    @staticmethod
    def get_all(include_unpublished=False):
        q = Announcement.query
        if not include_unpublished:
            q = q.filter_by(published=True)
        return q.order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).all()

    @staticmethod
    def get_by_id(ann_id):
        return Announcement.query.get(ann_id)

    @staticmethod
    def create(title, content, competition_id=None, scheduled_at=None, pinned=False, published=True, visibility="public"):
        ann = Announcement(
            title=title,
            content=content,
            competition_id=competition_id,
            scheduled_at=scheduled_at,
            pinned=pinned,
            published=published,
            visibility=visibility
        )
        db.session.add(ann)
        safe_commit()
        return ann

    @staticmethod
    def update(ann_id, **kwargs):
        ann = Announcement.query.get(ann_id)
        if ann:
            for k, v in kwargs.items():
                if hasattr(ann, k):
                    setattr(ann, k, v)
            safe_commit()
        return ann

    @staticmethod
    def delete(ann_id):
        ann = Announcement.query.get(ann_id)
        if ann:
            db.session.delete(ann)
            safe_commit()
            return True
        return False
