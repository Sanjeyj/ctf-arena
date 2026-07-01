from app.utils.legacy import load_scores, save_scores, get_participant_solved
import datetime

class SubmissionRepository:
    @staticmethod
    def get_solved_by_user(username):
        return get_participant_solved(username)

    @staticmethod
    def add_solve(username, ch_id, points, elapsed):
        data = load_scores()
        participant = data["participants"].setdefault(username, {
            "registered_at": datetime.datetime.now().isoformat(),
            "solved": {}
        })
        solved = participant.setdefault("solved", {})
        
        solved[ch_id] = {
            "time": datetime.datetime.now().isoformat(),
            "points": points,
            "elapsed": elapsed
        }
        save_scores(data)
        return solved[ch_id]

    @staticmethod
    def reset_user_solves(username):
        data = load_scores()
        if username in data["participants"]:
            data["participants"][username]["solved"] = {}
            data["participants"][username]["registered_at"] = datetime.datetime.now().isoformat()
            save_scores(data)
            return True
        return False

    @staticmethod
    def reset_all_solves():
        save_scores({"participants": {}})
        return True
