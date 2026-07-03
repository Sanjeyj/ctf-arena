"""
Campaign Service - Phase 19 Security Research & CTI Platform.
Manages campaigns, actor profiles, affected sectors, techniques, and timelines.
"""
from app.extensions import db
from app.models.campaign import Campaign

class CampaignService:

    @staticmethod
    def create_campaign(actor_id: int, name: str, start_date=None, end_date=None,
                        target_sector: str = "", description: str = "",
                        malware_used: str = "", techniques_used: str = "",
                        org_id: int = None) -> Campaign:
        campaign = Campaign(
            actor_id=actor_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            target_sector=target_sector,
            description=description,
            malware_used=malware_used,
            techniques_used=techniques_used,
            organization_id=org_id
        )
        db.session.add(campaign)
        db.session.commit()
        return campaign

    @staticmethod
    def get_campaign(campaign_id: int) -> Campaign:
        return db.session.get(Campaign, campaign_id)

    @staticmethod
    def list_campaigns(org_id: int = None):
        q = Campaign.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()

    @staticmethod
    def update_campaign(campaign_id: int, **kwargs) -> Campaign:
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        for key, val in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, val)
        db.session.commit()
        return campaign

    @staticmethod
    def delete_campaign(campaign_id: int) -> bool:
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            return False
        db.session.delete(campaign)
        db.session.commit()
        return True
