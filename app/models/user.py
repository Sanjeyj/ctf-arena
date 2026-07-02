import datetime
import json
from flask_login import UserMixin
from app.extensions import db, utcnow
from app.models.mixins import TimestampMixin, UUIDMixin, SoftDeleteMixin, TenantMixin

class User(db.Model, UserMixin, TimestampMixin, UUIDMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'users'

    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    registered_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    
    # Extended identity fields
    display_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), nullable=True, unique=True, index=True)
    password_hash = db.Column(db.String(128), nullable=True)
    
    # Session & Lockout fields
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    last_ip = db.Column(db.String(45), nullable=True)
    
    # Profile information
    profile_image = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    preferred_theme = db.Column(db.String(50), nullable=True)
    
    # Verification and reset tokens (Framework only)
    email_verification_token = db.Column(db.String(100), nullable=True, unique=True, index=True)
    email_verification_expires_at = db.Column(db.DateTime, nullable=True)
    
    password_reset_token = db.Column(db.String(100), nullable=True, unique=True, index=True)
    password_reset_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Preferences JSON mapping stored as Text
    _preferences = db.Column('preferences', db.Text, nullable=True)
    
    # Foreign Keys & Relationships
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Many-to-many relationship with Role
    roles = db.relationship(
        'Role',
        secondary='user_roles',
        back_populates='users',
        lazy='joined'
    )
    
    submissions = db.relationship('Submission', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', backref='user', lazy=True, cascade='all, delete-orphan')
    
    @property
    def preferences(self):
        if self._preferences:
            try:
                return json.loads(self._preferences)
            except Exception:
                return {}
        return {}

    @preferences.setter
    def preferences(self, value):
        self._preferences = json.dumps(value or {})

    # Compatibility property to keep existing codes querying user.role working
    @property
    def role(self):
        if self.roles:
            return self.roles[0].name
        return "Participant"
