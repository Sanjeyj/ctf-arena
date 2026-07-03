"""
DigitalTwin Service - Phase 23 Security Digital Twin.
Simulates security incidents impact ratings, ransomware propagation, and controls failures.
"""
from app.extensions import db
from app.models.asset import Asset
from app.models.compliance_control import ComplianceControl
from app.models.digital_twin import DigitalTwin

class DigitalTwinService:

    @staticmethod
    def simulate_asset_failure(asset_id: int) -> dict:
        asset = db.session.get(Asset, asset_id)
        criticality = asset.criticality if asset else 5
        
        impact = min(100.0, criticality * 10.0 + 15.0)
        risk = min(100.0, criticality * 10.0)
        recovery = max(4, criticality * 4)

        return {
            "scenario": "asset_failure",
            "asset_id": asset_id,
            "impact_score": impact,
            "risk_score": risk,
            "recovery_estimate_hours": recovery
        }

    @staticmethod
    def simulate_ransomware(asset_id: int, spread_factor: int = 2) -> dict:
        asset = db.session.get(Asset, asset_id)
        criticality = asset.criticality if asset else 5
        
        impact = min(100.0, (criticality * 10.0) * spread_factor)
        risk = min(100.0, 40.0 + (criticality * 5.0))
        recovery = max(12, criticality * spread_factor * 3)

        return {
            "scenario": "ransomware",
            "asset_id": asset_id,
            "impact_score": impact,
            "risk_score": risk,
            "recovery_estimate_hours": recovery
        }

    @staticmethod
    def simulate_control_failure(control_id: int) -> dict:
        control = db.session.get(ComplianceControl, control_id)
        # Base failure weight
        impact = 45.0 if not control else (75.0 if control.status == 'failed' else 55.0)
        risk = 60.0
        recovery = 8

        return {
            "scenario": "control_failures",
            "control_id": control_id,
            "impact_score": impact,
            "risk_score": risk,
            "recovery_estimate_hours": recovery
        }
