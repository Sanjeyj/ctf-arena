# Telegram Notifications Plugin
def on_team_create(team, creator):
    print(f"[TelegramNotifications] New team created! '{team.name}' founded by '{creator.username}'")

def setup(api):
    api.register_hook("after_team_create", on_team_create)
