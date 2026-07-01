from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Theme(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'themes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False, index=True)
    settings = db.Column(db.Text, nullable=True) # JSON or config string
