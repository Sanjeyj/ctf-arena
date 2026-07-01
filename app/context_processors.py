from flask import session

def utility_processors():
    return {
        "platform_name": "CTF Arena",
        "competition_name": "Easy CTF Challenge",
        "logo_emoji": "🚩",
        "active_theme": "default",
        "current_user_name": session.get("user"),
        "platform_version": "v2",
        "notifications_count": 0
    }
