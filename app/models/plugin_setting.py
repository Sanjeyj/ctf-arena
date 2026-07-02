from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class PluginSetting(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'plugin_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    plugin_installation_id = db.Column(db.Integer, db.ForeignKey('plugin_installations.id', ondelete='CASCADE'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)
