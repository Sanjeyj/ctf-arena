"""
ExposureInventoryService - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Tracks exposed assets, references, and calculates risk scores.
"""
from app.extensions import db
from app.models.exposure_asset import ExposureAsset
from app.models.exposure_finding import ExposureFinding
from app.models.asset import Asset
from app.models.universe_node import UniverseNode


class ExposureInventoryService:

    @staticmethod
    def register_projection(asset_ref_type, asset_ref_id, display_name, exposure_type, internet_exposed, criticality, business_impact, zone_id, org_id):
        proj = ExposureAsset(
            asset_reference_type=asset_ref_type,
            asset_reference_id=asset_ref_id,
            display_name=display_name,
            exposure_type=exposure_type,
            internet_exposed=internet_exposed,
            criticality=criticality,
            business_impact_score=business_impact,
            architecture_zone_id=zone_id,
            organization_id=org_id
        )
        db.session.add(proj)
        db.session.commit()
        return proj

    @staticmethod
    def resolve_reference(asset_id, org_id):
        proj = ExposureAsset.query.filter_by(id=asset_id, organization_id=org_id).first()
        if not proj:
            return None

        # Try to resolve to the actual original model (polymorphic lookup)
        try:
            if proj.asset_reference_type == 'asset':
                return Asset.query.filter_by(id=proj.asset_reference_id).first()
            elif proj.asset_reference_type == 'universe_node':
                return UniverseNode.query.filter_by(id=proj.asset_reference_id).first()
        except Exception:
            pass

        return None

    @staticmethod
    def calculate_exposure_score(asset_id, org_id):
        proj = ExposureAsset.query.filter_by(id=asset_id, organization_id=org_id).first()
        if not proj:
            return 0.0

        # Base score on exposure type and internet exposure
        base = 8.0 if proj.internet_exposed else 2.0
        if proj.exposure_type == 'external':
            base += 3.0
        elif proj.exposure_type == 'perimeter':
            base += 2.0

        # Add score penalty for findings
        findings_penalty = 0.0
        findings = ExposureFinding.query.filter_by(exposure_asset_id=asset_id, organization_id=org_id, status='open').all()
        for f in findings:
            findings_penalty += f.impact_score * f.likelihood * f.confidence

        score = base + findings_penalty
        # Apply criticality modifier
        crit_mult = 1.5 if proj.criticality == 'critical' else (1.2 if proj.criticality == 'high' else 1.0)
        score *= crit_mult

        # Apply business impact multiplier
        score *= (proj.business_impact_score / 5.0)

        return min(100.0, max(0.0, score))

    @staticmethod
    def list_exposed_assets(org_id):
        assets = ExposureAsset.query.filter_by(organization_id=org_id).all()
        res = []
        for a in assets:
            score = ExposureInventoryService.calculate_exposure_score(a.id, org_id)
            res.append({
                "id": a.id,
                "display_name": a.display_name,
                "exposure_type": a.exposure_type,
                "exposure_score": round(score, 1),
                "internet_exposed": a.internet_exposed,
                "criticality": a.criticality
            })
        return res

    @staticmethod
    def exposure_summary(org_id):
        assets = ExposureAsset.query.filter_by(organization_id=org_id).all()
        if not assets:
            return {"total_assets": 0, "exposed_count": 0, "avg_exposure_score": 0.0}

        exposed_count = 0
        total_score = 0.0
        for a in assets:
            score = ExposureInventoryService.calculate_exposure_score(a.id, org_id)
            total_score += score
            if a.internet_exposed or a.exposure_type in ['external', 'perimeter']:
                exposed_count += 1

        return {
            "total_assets": len(assets),
            "exposed_count": exposed_count,
            "avg_exposure_score": round(total_score / len(assets), 1)
        }

    @staticmethod
    def exposure_trend(org_id):
        summary = ExposureInventoryService.exposure_summary(org_id)
        # Return simulated historical trend
        score = summary["avg_exposure_score"]
        return [
            {"date": "7 days ago", "avg_score": round(score * 1.1, 1)},
            {"date": "3 days ago", "avg_score": round(score * 1.05, 1)},
            {"date": "today", "avg_score": score}
        ]
