from app.extensions import db
from app.models.deployment_profile import DeploymentProfile


class DeploymentProfileRepository:
    """CRUD access for DeploymentProfile records."""

    @staticmethod
    def get_all():
        return DeploymentProfile.query.order_by(DeploymentProfile.name).all()

    @staticmethod
    def get_by_id(profile_id):
        return DeploymentProfile.query.get(profile_id)

    @staticmethod
    def get_by_name(name):
        return DeploymentProfile.query.filter_by(name=name).first()

    @staticmethod
    def create(**kwargs):
        profile = DeploymentProfile(**kwargs)
        db.session.add(profile)
        db.session.commit()
        return profile

    @staticmethod
    def update(profile_id, **kwargs):
        profile = DeploymentProfile.query.get(profile_id)
        if not profile:
            return None
        for k, v in kwargs.items():
            setattr(profile, k, v)
        db.session.commit()
        return profile

    @staticmethod
    def delete(profile_id):
        profile = DeploymentProfile.query.get(profile_id)
        if profile:
            db.session.delete(profile)
            db.session.commit()
        return profile
