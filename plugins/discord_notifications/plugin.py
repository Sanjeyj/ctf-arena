# Discord Notifications Plugin
def on_submission(user, challenge, correct, submitted_flag):
    if correct:
        print(f"[DiscordNotifications] SOLVE! Player '{user.username}' solved '{challenge.title}'")
    else:
        print(f"[DiscordNotifications] FAIL. Player '{user.username}' attempted '{challenge.title}'")

def setup(api):
    api.register_hook("after_submission", on_submission)
