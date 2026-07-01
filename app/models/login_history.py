import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class LoginHistory(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'login_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, default=False, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
