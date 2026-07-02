from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin

class PluginInstallation(db.Model, TimestampMixin, UUIDMixin):
    __tablename__ = 'plugin_installations'
    
    id = db.Column(db.Integer, primary_key=True)
    plugin_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    version = db.Column(db.String(30), nullable=False)
    author = db.Column(db.String(100), nullable=True)
    enabled = db.Column(db.Boolean, default=False, nullable=False, index=True)
    zip_path = db.Column(db.String(255), nullable=True)
    
    # Relationships
    permissions = db.relationship('PluginPermission', backref='plugin', cascade='all, delete-orphan')
    settings = db.relationship('PluginSetting', backref='plugin', cascade='all, delete-orphan')
