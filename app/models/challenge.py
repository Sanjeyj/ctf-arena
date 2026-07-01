from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin, SoftDeleteMixin
import datetime

class Challenge(db.Model, TimestampMixin, UUIDMixin, SoftDeleteMixin):
    __tablename__ = 'challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    legacy_id = db.Column(db.String(20), unique=True, nullable=False, index=True) # e.g. "ch1"
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(10), nullable=True)
    difficulty = db.Column(db.String(20), nullable=False)
    
    # Extended CMS Fields
    type = db.Column(db.String(50), default="standard", nullable=False) # e.g. standard, dynamic
    state = db.Column(db.String(20), default="visible", nullable=False, index=True) # visible, hidden, archived, locked
    visible = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Scoring configurations
    initial_points = db.Column(db.Integer, default=50, nullable=False)
    minimum_points = db.Column(db.Integer, default=10, nullable=False)
    current_points = db.Column(db.Integer, default=50, nullable=False)
    decay_type = db.Column(db.String(20), default="static", nullable=False) # static, linear, logarithmic
    decay_rate = db.Column(db.Integer, default=0, nullable=False) # e.g. solve threshold limit
    
    # Attempt controls
    max_attempts = db.Column(db.Integer, default=0, nullable=False) # 0 means unlimited
    requires_connection_info = db.Column(db.Boolean, default=False, nullable=False)
    connection_info = db.Column(db.String(255), nullable=True)
    docker_image = db.Column(db.String(255), nullable=True) # Placeholder
    
    # Statistics trackers
    download_count = db.Column(db.Integer, default=0, nullable=False)
    solve_count = db.Column(db.Integer, default=0, nullable=False)
    attempt_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Display configuration
    display_order = db.Column(db.Integer, default=0, nullable=False)
    featured = db.Column(db.Boolean, default=False, nullable=False)
    archived = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id', ondelete='SET NULL'), nullable=True, index=True)
    
    flags = db.relationship('Flag', backref='challenge', lazy=True, cascade='all, delete-orphan')
    hints = db.relationship('Hint', backref='challenge', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('ChallengeFile', backref='challenge', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='challenge', lazy=True, cascade='all, delete-orphan')
