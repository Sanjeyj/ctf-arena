"""
Risk Service - Phase 22 Risk Engine.
Calculates severity risk tiers (LOW, MEDIUM, HIGH, CRITICAL) for assets, users, and organizations.
"""
from app.extensions import db
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.asset import Asset
from app.models.user import User

class RiskService:

    @staticmethod
    def calculate_asset_risk(asset_id: int) -> str:
        asset = db.session.get(Asset, asset_id)
        if not asset:
            return "LOW"
            
        # Base risk calculation on asset criticality weight
        score = asset.criticality * 10
        
        # Pull associated alerts count to escalate score
        alert_count = Alert.query.count()
        score += (alert_count * 5)
        
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 35:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def calculate_user_risk(user_id: int) -> str:
        user = db.session.get(User, user_id)
        if not user:
            return "LOW"
            
        incident_count = Incident.query.filter_by(assigned_to=user.username).count()
        score = incident_count * 20
        
        if score >= 75:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 25:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def calculate_organization_risk(org_id: int) -> str:
        # Sum incidents and alert counts
        incident_count = Incident.query.count()
        alert_count = Alert.query.count()
        score = (incident_count * 15) + (alert_count * 5)
        
        if score >= 80:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 25:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def calculate_threat_risk() -> str:
        # Base threat intelligence level calculation
        alert_count = Alert.query.count()
        if alert_count > 10:
            return "CRITICAL"
        elif alert_count > 5:
            return "HIGH"
        elif alert_count > 2:
            return "MEDIUM"
        return "LOW"
