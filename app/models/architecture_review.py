"""
ArchitectureReview model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class ArchitectureReview(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'architecture_reviews'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    scope = db.Column(db.String(255), nullable=False)
    review_type = db.Column(db.String(100), nullable=False, default='annual')  # continuous, annual, adhoc
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    findings_count = db.Column(db.Integer, nullable=False, default=0)
    decision = db.Column(db.String(50), nullable=False, default='pending')  # approved, rejected, deferred, pending
    reviewer = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='in_progress')
    reviewed_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    summary = db.Column(db.Text, nullable=True)
