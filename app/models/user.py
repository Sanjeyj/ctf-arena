# User model skeleton for future SQLAlchemy integration
class User:
    def __init__(self, id=None, username=None, role="Participant"):
        self.id = id
        self.username = username
        self.role = role
