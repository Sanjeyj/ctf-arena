from app.repositories.user_repository import UserRepository

class UserService:
    @staticmethod
    def get_user(username):
        return UserRepository.get_by_name(username)
