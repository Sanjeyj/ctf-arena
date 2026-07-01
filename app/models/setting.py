from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class Setting(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), default='config', nullable=False, index=True)
