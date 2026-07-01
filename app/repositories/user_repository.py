from app.utils.legacy import load_scores, save_scores
import datetime

class UserRepository:
    @staticmethod
    def get_by_name(username):
        data = load_scores()
        if username in data["participants"]:
            return {
                "name": username,
                "registered_at": data["participants"][username].get("registered_at")
            }
        return None

    @staticmethod
    def create(username):
        data = load_scores()
        if username not in data["participants"]:
            data["participants"][username] = {
                "registered_at": datetime.datetime.now().isoformat(),
                "solved": {}
            }
            save_scores(data)
        return {
            "name": username,
            "registered_at": data["participants"][username].get("registered_at")
        }
