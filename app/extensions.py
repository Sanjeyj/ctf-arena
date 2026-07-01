from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def safe_commit():
    """Commit the current DB session; rollback and re-raise on any error.
    
    Use this in place of db.session.commit() for all write operations so that
    a failed flush never leaves the session in a broken transaction state.
    """
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

