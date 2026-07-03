"""
Threat Actor Service - Phase 19 Security Research & CTI Platform.
Curates actor profiles, motivations, sectors, and MITRE ATT&CK technique coverages.
"""
from app.extensions import db
from app.models.threat_actor import ThreatActor

class ThreatActorService:

    @staticmethod
    def create_actor(name: str, aliases: str = "", country: str = "",
                     motivation: str = "", sophistication: str = "",
                     org_id: int = None) -> ThreatActor:
        actor = ThreatActor(
            name=name,
            aliases=aliases,
            country=country,
            motivation=motivation,
            sophistication=sophistication,
            organization_id=org_id
        )
        db.session.add(actor)
        db.session.commit()
        return actor

    @staticmethod
    def get_actor(actor_id: int) -> ThreatActor:
        return db.session.get(ThreatActor, actor_id)

    @staticmethod
    def list_actors(org_id: int = None):
        q = ThreatActor.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()

    @staticmethod
    def update_actor(actor_id: int, **kwargs) -> ThreatActor:
        actor = db.session.get(ThreatActor, actor_id)
        if not actor:
            raise ValueError(f"Threat Actor {actor_id} not found")
        for key, val in kwargs.items():
            if hasattr(actor, key):
                setattr(actor, key, val)
        db.session.commit()
        return actor

    @staticmethod
    def delete_actor(actor_id: int) -> bool:
        actor = db.session.get(ThreatActor, actor_id)
        if not actor:
            return False
        db.session.delete(actor)
        db.session.commit()
        return True
