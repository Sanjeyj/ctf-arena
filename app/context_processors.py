from flask_login import current_user
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository

def utility_processors():
    solved = {}
    challenges = {}
    username = None
    
    if current_user.is_authenticated:
        username = current_user.username
        
        # Load active visible challenges only
        challenges_list = ChallengeRepository.get_all(include_hidden=False)
        for ch in challenges_list:
            challenges[ch.legacy_id] = {
                "id": ch.legacy_id,
                "title": ch.title,
                "category": ch.category.name if ch.category else "General",
                "points": ch.current_points,
                "icon": ch.icon,
                "difficulty": ch.difficulty,
                "description": ch.description
            }
        
        # Load user solves
        solved_list = SubmissionRepository.get_solved_by_user(username)
        for sub in solved_list:
            sch = next((c for c in challenges_list if c.id == sub.challenge_id), None)
            if sch:
                solved[sch.legacy_id] = {
                    "points": sub.points,
                    "time": sub.time.isoformat(),
                    "elapsed": sub.elapsed
                }
                
    return {
        "platform_name": "CTF Arena",
        "competition_name": "Easy CTF Challenge",
        "logo_emoji": "🚩",
        "active_theme": "default",
        "current_user_name": username,
        "username": username,
        "solved": solved,
        "challenges": challenges,
        "platform_version": "v2",
        "notifications_count": 0
    }
