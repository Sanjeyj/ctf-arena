"""
Asset Service - Phase 22 Asset Management.
Manages network assets inventory mapping, tags assignment, and criticality querying.
"""
from app.extensions import db
from app.models.asset import Asset
from app.models.asset_tag import AssetTag
from app.services.risk_service import RiskService

class AssetService:

    @staticmethod
    def discover(name: str, type_label: str = 'server', criticality: int = 5,
                 ip_address: str = None, org_id: int = None) -> Asset:
        asset = Asset(
            name=name,
            type_label=type_label,
            criticality=criticality,
            ip_address=ip_address,
            organization_id=org_id
        )
        db.session.add(asset)
        db.session.commit()
        return asset

    @staticmethod
    def calculate_risk(asset_id: int) -> str:
        asset = db.session.get(Asset, asset_id)
        if not asset:
            raise ValueError(f"Asset #{asset_id} not found")
        risk = RiskService.calculate_asset_risk(asset_id)
        asset.risk_level = risk
        db.session.commit()
        return risk

    @staticmethod
    def assign_tags(asset_id: int, tags: dict, org_id: int = None) -> list[AssetTag]:
        # Delete existing tags
        AssetTag.query.filter_by(asset_id=asset_id).delete()
        
        tag_instances = []
        for k, v in tags.items():
            t = AssetTag(asset_id=asset_id, key=k, value=v, organization_id=org_id)
            db.session.add(t)
            tag_instances.append(t)
            
        db.session.commit()
        return tag_instances

    @staticmethod
    def critical_assets(org_id: int = None) -> list[Asset]:
        """Fetch high criticality level targets (criticality threshold >= 7)."""
        q = Asset.query.filter(Asset.criticality >= 7)
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()
