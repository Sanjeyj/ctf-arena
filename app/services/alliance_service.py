"""
AllianceService - Phase 28 Cyber Civilization Platform.
Manages cyber nation defense alliances and synchronizes member node health monitoring.
"""
from app.extensions import db
from app.models.defense_alliance import DefenseAlliance
from app.models.defense_grid import DefenseGrid


class AllianceService:
    @staticmethod
    def create(name: str, members: list, org_id: int) -> DefenseAlliance:
        """Create and register a new trans-national defense alliance."""
        alliance = DefenseAlliance(
            alliance_name=name,
            members=",".join(members),
            trust_score=0.6,
            status='active',
            organization_id=org_id
        )
        db.session.add(alliance)
        db.session.commit()
        return alliance

    @staticmethod
    def validate(alliance_id: int) -> dict:
        """Check the status integrity and validity of an alliance."""
        alliance = db.session.get(DefenseAlliance, alliance_id)
        if not alliance:
            return {'valid': False, 'reason': f'Alliance {alliance_id} not found'}
        
        member_list = [m.strip() for m in alliance.members.split(',')] if alliance.members else []
        valid = alliance.status == 'active' and len(member_list) >= 2
        return {
            'alliance_id': alliance_id,
            'valid': valid,
            'member_count': len(member_list),
            'trust_score': alliance.trust_score,
            'status': alliance.status
        }

    @staticmethod
    def synchronize(org_id: int) -> dict:
        """Sync defense grid statuses across all alliances under the tenant."""
        alliances = DefenseAlliance.query.filter_by(organization_id=org_id, status='active').all()
        grids = DefenseGrid.query.filter_by(organization_id=org_id).all()
        
        total_grids = len(grids)
        healthy_grids = sum(1 for g in grids if g.health >= 0.8)
        sync_rate = (healthy_grids / total_grids * 100.0) if total_grids > 0 else 100.0
        
        return {
            'alliances_synced': len(alliances),
            'total_defense_grids': total_grids,
            'synchronized_percentage': round(sync_rate, 1),
            'status': 'operational' if sync_rate >= 80.0 else 'degraded'
        }
