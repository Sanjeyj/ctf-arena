import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ctf_super_secret_2024")
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ctf_admin_2024")
    SCORES_FILE = os.environ.get("SCORES_FILE", "scores.json")
    
    # Future expansions
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///instance/ctf.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)) # 16MB default

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SCORES_FILE = "tests/scores_test.json"

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
