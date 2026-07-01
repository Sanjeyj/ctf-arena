from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Plugin(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'plugins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    enabled = db.Column(db.Boolean, default=False, nullable=False, index=True)
    config = db.Column(db.Text, nullable=True) # JSON config
