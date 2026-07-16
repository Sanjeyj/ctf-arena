import sys
import os

# Add root folder to path so app package can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

env = os.environ.get("FLASK_ENV", "production")
app = create_app(env)
