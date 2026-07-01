from app.utils.legacy import CHALLENGES

class ChallengeRepository:
    @staticmethod
    def get_all():
        return CHALLENGES

    @staticmethod
    def get_by_id(ch_id):
        return CHALLENGES.get(ch_id)
