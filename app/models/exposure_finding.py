"""
ExposureFinding model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class ExposureFinding(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'exposure_findings'

    id = db.Column(db.Integer, primary_key=True)
    exposure_asset_id = db.Column(db.Integer, db.ForeignKey('exposure_assets.id', name='fk_exposure_findings_exposure_asset_id'), nullable=False)
    finding_type = db.Column(db.String(100), nullable=False)  # vulnerability, misconfiguration, open_port, credentials_leak
    title = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(50), nullable=False, default='medium')  # low, medium, high, critical
    likelihood = db.Column(db.Float, nullable=False, default=0.5)
    impact_score = db.Column(db.Float, nullable=False, default=5.0)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    status = db.Column(db.String(50), nullable=False, default='open')  # open, mitigated, accepted, false_positive
    source_type = db.Column(db.String(100), nullable=False, default='simulation')  # simulation, synthetic_import, control_gap, sbom_metadata, attestation_gap, architecture_review
    first_seen_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_seen_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    metadata_json = db.Column(db.Text, nullable=True, default='{}')

    # Relationships
    remediation_plans = db.relationship('RemediationPlan', backref='finding', lazy=True, cascade='all, delete-orphan')
