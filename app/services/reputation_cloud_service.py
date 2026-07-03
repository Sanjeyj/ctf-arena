"""
Reputation Cloud Service - Phase 24 Global Cyber Security Cloud.
Computes global threat actor reputational scoring ranks and aggregates entity feedback.
"""
from app.extensions import db
from app.models.threat_reputation import ThreatReputation

class ReputationCloudService:
    @staticmethod
    def get_reputation(entity_value: str, organization_id: int = None) -> ThreatReputation:
        """Query reputation score record for an indicator, IP, or threat actor."""
        query = ThreatReputation.query.filter_by(entity_value=entity_value)
        if organization_id is not None:
            query = ThreatReputation.tenant_filter(query, organization_id)
        return query.first()

    @staticmethod
    def update_reputation(entity_value: str, score: int, level: str = None, category: str = 'ioc', organization_id: int = None) -> ThreatReputation:
        """Update or register threat indicator score ratings (0-100)."""
        reputation = ReputationCloudService.get_reputation(entity_value, organization_id)
        
        # Calculate level based on score if not specified
        if not level:
            if score >= 80:
                level = 'critical'
            elif score >= 60:
                level = 'high'
            elif score >= 40:
                level = 'medium'
            else:
                level = 'low'

        if not reputation:
            reputation = ThreatReputation(
                entity_value=entity_value,
                category=category,
                score=score,
                level=level,
                organization_id=organization_id
            )
            db.session.add(reputation)
        else:
            reputation.score = score
            reputation.level = level
            reputation.category = category
        
        db.session.commit()
        return reputation

    @staticmethod
    def submit_feedback(entity_value: str, rating: int, feedback_category: str = 'ioc', organization_id: int = None) -> ThreatReputation:
        """Feed indicator feedback ratings to adjust reputation score."""
        reputation = ReputationCloudService.get_reputation(entity_value, organization_id)
        if not reputation:
            # Create a default reputation score of 50
            reputation = ReputationCloudService.update_reputation(
                entity_value=entity_value,
                score=50,
                category=feedback_category,
                organization_id=organization_id
            )
        
        # Adjust reputation score based on feedback rating (-10 to +10 change)
        new_score = max(0, min(100, reputation.score + rating))
        return ReputationCloudService.update_reputation(
            entity_value=entity_value,
            score=new_score,
            category=reputation.category,
            organization_id=organization_id
        )

    @staticmethod
    def bulk_lookup(entities: list, organization_id: int = None) -> list:
        """Perform bulk lookup of reputation scores."""
        results = []
        for entity in entities:
            rep = ReputationCloudService.get_reputation(entity, organization_id)
            if rep:
                results.append(rep.to_dict())
            else:
                results.append({
                    'entity_value': entity,
                    'score': 50,
                    'level': 'medium',
                    'category': 'unknown'
                })
        return results
