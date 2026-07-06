"""
AttackPath model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class AttackPath(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'attack_paths'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    source_asset_id = db.Column(db.Integer, db.ForeignKey('exposure_assets.id', name='fk_attack_paths_source_asset_id'), nullable=False)
    target_asset_id = db.Column(db.Integer, db.ForeignKey('exposure_assets.id', name='fk_attack_paths_target_asset_id'), nullable=False)
    path_json = db.Column(db.Text, nullable=False, default='[]')
    hop_count = db.Column(db.Integer, nullable=False, default=0)
    path_risk_score = db.Column(db.Float, nullable=False, default=0.0)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    status = db.Column(db.String(50), nullable=False, default='active')
    calculated_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
