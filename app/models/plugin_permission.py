from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class PluginPermission(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'plugin_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    plugin_installation_id = db.Column(db.Integer, db.ForeignKey('plugin_installations.id', ondelete='CASCADE'), nullable=False)
    permission_name = db.Column(db.String(100), nullable=False)
    granted = db.Column(db.Boolean, default=False, nullable=False)
