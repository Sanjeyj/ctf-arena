from app.repositories.announcement_repository import AnnouncementRepository
import datetime
from app.extensions import utcnow

class AnnouncementService:
    @staticmethod
    def get_active_announcements():
        now = utcnow()
        all_anns = AnnouncementRepository.get_all(include_unpublished=False)
        active = []
        for ann in all_anns:
            # Filter by scheduling date if set
            if ann.scheduled_at and ann.scheduled_at > now:
                continue
            active.append(ann)
        return active

    @staticmethod
    def create_announcement(title, content, **kwargs):
        if not title or not content:
            return None, "Title and Content are required."
        # Map public-facing 'visible' to model field 'published'
        if 'visible' in kwargs:
            kwargs['published'] = kwargs.pop('visible')
        ann = AnnouncementRepository.create(title, content, **kwargs)
        return ann, None

    @staticmethod
    def update_announcement(ann_id, **kwargs):
        return AnnouncementRepository.update(ann_id, **kwargs)

    @staticmethod
    def delete_announcement(ann_id):
        return AnnouncementRepository.delete(ann_id)
