from app.extensions import db
from app.models.organization import Organization
from app.models.user import User
from app.models.competition import Competition
from app.models.challenge import Challenge
from app.models.challenge_instance import ChallengeInstance
from app.models.challenge_file import ChallengeFile
from app.models.ai_hint_request import AIHintRequest
from app.models.ai_writeup import AIWriteup
from app.models.ai_conversation import AIConversation
from app.models.ai_difficulty_prediction import AIDifficultyPrediction

class QuotaService:
    @staticmethod
    def get_usage(org: Organization, resource: str) -> int:
        """Calculate the current usage of the specified resource for the organization."""
        if resource == 'users':
            return User.query.filter_by(organization_id=org.id, is_deleted=False).count()
        elif resource == 'competitions':
            return Competition.query.filter_by(organization_id=org.id).count()
        elif resource == 'challenges':
            return Challenge.query.filter_by(organization_id=org.id, is_deleted=False).count()
        elif resource == 'containers':
            return ChallengeInstance.query.join(User).filter(
                User.organization_id == org.id,
                ChallengeInstance.status == 'running'
            ).count()
        elif resource == 'ai_tokens':
            hint_tokens = db.session.query(db.func.sum(AIHintRequest.tokens_used))\
                .join(User).filter(User.organization_id == org.id).scalar() or 0
            writeup_tokens = db.session.query(db.func.sum(AIWriteup.tokens_used))\
                .join(User).filter(User.organization_id == org.id).scalar() or 0
            conv_tokens = db.session.query(db.func.sum(AIConversation.tokens_used))\
                .join(User).filter(User.organization_id == org.id).scalar() or 0
            pred_tokens = db.session.query(db.func.sum(AIDifficultyPrediction.tokens_used))\
                .join(Challenge).filter(Challenge.organization_id == org.id).scalar() or 0
            return int(hint_tokens + writeup_tokens + conv_tokens + pred_tokens)
        elif resource == 'storage_mb':
            total_bytes = db.session.query(db.func.sum(ChallengeFile.size))\
                .join(Challenge).filter(Challenge.organization_id == org.id).scalar() or 0
            return round(total_bytes / (1024 * 1024), 2)
        return 0

    @classmethod
    def check(cls, org: Organization, resource: str) -> tuple[bool, int, int]:
        """
        Check if the organization is within its quota for a resource.
        Returns (allowed, limit, used).
        """
        limit = org.get_quota(resource)
        if limit == -1:  # Unlimited
            return True, limit, cls.get_usage(org, resource)
        
        used = cls.get_usage(org, resource)
        return used < limit, limit, used
