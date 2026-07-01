from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin
import datetime

class Category(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Extended CMS Fields
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(20), default="#00f0ff", nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    visible = db.Column(db.Boolean, default=True, nullable=False)
    
    challenges = db.relationship('Challenge', backref='category', lazy=True)
