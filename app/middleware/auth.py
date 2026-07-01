# Auth middleware placeholder
class AuthMiddleware:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)
            
    def init_app(self, app):
        pass
