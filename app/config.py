import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ctf_super_secret_2024")
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ctf_admin_2024")
    SCORES_FILE = os.environ.get("SCORES_FILE", "scores.json")
    
    # Database
    _db_url = os.environ.get("DATABASE_URL")
    if os.environ.get("VERCEL"):
        if not _db_url or "db.example.com" in _db_url or "example.com" in _db_url:
            _db_url = "sqlite:////tmp/ctf.db"
    
    SQLALCHEMY_DATABASE_URI = _db_url or (
        "sqlite:///" + os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance", "ctf.db"))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    if os.environ.get("VERCEL"):
        if _redis_url and ("redis.example.com" in _redis_url or "example.com" in _redis_url):
            _redis_url = None
    REDIS_URL = _redis_url
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
    PREFERRED_URL_SCHEME = 'http'
    TRUSTED_PROXIES = int(os.environ.get("TRUSTED_PROXIES", "0"))
    ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "*").split(",") if h.strip()]

    # Rate Limiting & Metrics
    WTF_CSRF_ENABLED = True
    METRICS_ENABLED = os.environ.get("METRICS_ENABLED", "True") == "True"
    RATE_LIMIT_LOGIN = os.environ.get("RATE_LIMIT_LOGIN", "5 per minute")
    RATE_LIMIT_SUBMIT = os.environ.get("RATE_LIMIT_SUBMIT", "10 per minute")
    RATE_LIMIT_API = os.environ.get("RATE_LIMIT_API", "60 per minute")
    RATE_LIMIT_GLOBAL = os.environ.get("RATE_LIMIT_GLOBAL", "100 per minute")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SCORES_FILE = "tests/scores_test.json"
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False # Disable CSRF for testing convenience in unittest client requests


class StagingConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'
    TRUSTED_PROXIES = int(os.environ.get("TRUSTED_PROXIES", "1"))


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'
    TRUSTED_PROXIES = int(os.environ.get("TRUSTED_PROXIES", "1"))


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
