import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ctf_super_secret_2024")
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ctf_admin_2024")
    SCORES_FILE = os.environ.get("SCORES_FILE", "scores.json")
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance", "ctf.db"))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)) # 16MB default

    # Password Policy Configuration
    PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", 8))
    PASSWORD_REQUIRE_UPPER = os.environ.get("PASSWORD_REQUIRE_UPPER", "True") == "True"
    PASSWORD_REQUIRE_LOWER = os.environ.get("PASSWORD_REQUIRE_LOWER", "True") == "True"
    PASSWORD_REQUIRE_DIGIT = os.environ.get("PASSWORD_REQUIRE_DIGIT", "True") == "True"
    PASSWORD_REQUIRE_SPECIAL = os.environ.get("PASSWORD_REQUIRE_SPECIAL", "True") == "True"

    # Security Configuration
    MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = int(os.environ.get("SESSION_LIFETIME_SECONDS", 1800)) # 30 mins default

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SCORES_FILE = "tests/scores_test.json"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False # Disable CSRF for testing convenience in unittest client requests

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
