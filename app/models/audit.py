from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class AuditLog(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True)
