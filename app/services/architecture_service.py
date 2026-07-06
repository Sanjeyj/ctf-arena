"""
ArchitectureService - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Handles security zones, trust boundaries, validations, mapping, and summaries.
"""
from app.extensions import db
from app.models.architecture_zone import ArchitectureZone
from app.models.trust_boundary import TrustBoundary
from app.models.exposure_asset import ExposureAsset
from app.models.control_validation import ControlValidation
import json


class ArchitectureService:

    @staticmethod
    def create_zone(name, zone_type, description, trust_level, criticality, org_id):
        zone = ArchitectureZone(
            name=name,
            zone_type=zone_type,
            description=description,
            trust_level=trust_level,
            criticality=criticality,
            organization_id=org_id
        )
        db.session.add(zone)
        db.session.commit()
        return zone

    @staticmethod
    def create_boundary(name, source_zone_id, target_zone_id, boundary_type, required_trust_score, control_requirements_json, org_id):
        boundary = TrustBoundary(
            name=name,
            source_zone_id=source_zone_id,
            target_zone_id=target_zone_id,
            boundary_type=boundary_type,
            required_trust_score=required_trust_score,
            control_requirements_json=control_requirements_json,
            organization_id=org_id
        )
        db.session.add(boundary)
        db.session.commit()
        return boundary

    @staticmethod
    def map_resource_to_zone(exposure_asset_id, zone_id, org_id):
        asset = ExposureAsset.query.filter_by(id=exposure_asset_id, organization_id=org_id).first()
        zone = ArchitectureZone.query.filter_by(id=zone_id, organization_id=org_id).first()
        if asset and zone:
            asset.architecture_zone_id = zone.id
            db.session.commit()
            return asset
        return None

    @staticmethod
    def validate_boundary(boundary_id, org_id):
        boundary = TrustBoundary.query.filter_by(id=boundary_id, organization_id=org_id).first()
        if not boundary:
            return {"status": "unknown", "gaps": []}

        # Check required control requirements against latest validations
        try:
            reqs = json.loads(boundary.control_requirements_json or '[]')
        except Exception:
            reqs = []

        gaps = []
        for req in reqs:
            # Look up validation for this control reference
            val = ControlValidation.query.filter_by(control_reference=req, organization_id=org_id).order_by(ControlValidation.id.desc()).first()
            if not val or val.status != 'valid':
                gaps.append(req)

        status = "valid" if not gaps else "violated"
        return {
            "status": status,
            "gaps": gaps
        }

    @staticmethod
    def architecture_summary(org_id):
        zones = ArchitectureZone.query.filter_by(organization_id=org_id).all()
        boundaries = TrustBoundary.query.filter_by(organization_id=org_id).all()

        violations_count = 0
        for b in boundaries:
            res = ArchitectureService.validate_boundary(b.id, org_id)
            if res["status"] == "violated":
                violations_count += 1

        return {
            "total_zones": len(zones),
            "total_boundaries": len(boundaries),
            "boundary_violations": violations_count
        }

    @staticmethod
    def identify_boundary_gaps(org_id):
        boundaries = TrustBoundary.query.filter_by(organization_id=org_id).all()
        gaps_list = []
        for b in boundaries:
            res = ArchitectureService.validate_boundary(b.id, org_id)
            if res["status"] == "violated":
                gaps_list.append({
                    "boundary_id": b.id,
                    "boundary_name": b.name,
                    "failing_controls": res["gaps"]
                })
        return gaps_list
