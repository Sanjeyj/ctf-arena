import datetime
from app.extensions import db, safe_commit
from app.models.challenge_instance import ChallengeInstance
from app.models.container_log import ContainerLog
from app.models.instance_snapshot import InstanceSnapshot


class ChallengeInstanceRepository:
    """CRUD access for ChallengeInstance, ContainerLog, and InstanceSnapshot."""

    # ------------------------------------------------------------------ #
    #  ChallengeInstance queries
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_by_id(instance_id):
        return ChallengeInstance.query.get(instance_id)

    @staticmethod
    def get_running_for_user(challenge_id, user_id):
        return (
            ChallengeInstance.query
            .filter_by(challenge_id=challenge_id, user_id=user_id)
            .filter(ChallengeInstance.status.in_(['creating', 'running']))
            .first()
        )

    @staticmethod
    def get_running_for_team(challenge_id, team_id):
        return (
            ChallengeInstance.query
            .filter_by(challenge_id=challenge_id, team_id=team_id)
            .filter(ChallengeInstance.status.in_(['creating', 'running']))
            .first()
        )

    @staticmethod
    def count_active_for_user(user_id):
        return (
            ChallengeInstance.query
            .filter_by(user_id=user_id)
            .filter(ChallengeInstance.status.in_(['creating', 'running']))
            .count()
        )

    @staticmethod
    def get_all_active():
        return (
            ChallengeInstance.query
            .filter(ChallengeInstance.status.in_(['creating', 'running']))
            .all()
        )

    @staticmethod
    def get_expired():
        now = datetime.datetime.utcnow()
        return (
            ChallengeInstance.query
            .filter(ChallengeInstance.status.in_(['creating', 'running']))
            .filter(ChallengeInstance.expires_at <= now)
            .all()
        )

    @staticmethod
    def get_for_challenge(challenge_id):
        return (
            ChallengeInstance.query
            .filter_by(challenge_id=challenge_id)
            .order_by(ChallengeInstance.created_at.desc())
            .all()
        )

    @staticmethod
    def create(challenge_id, docker_image_id=None, user_id=None, team_id=None,
                deployment_profile_id=None, ttl_minutes=30):
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=ttl_minutes)
        instance = ChallengeInstance(
            challenge_id=challenge_id,
            docker_image_id=docker_image_id,
            user_id=user_id,
            team_id=team_id,
            deployment_profile_id=deployment_profile_id,
            status='creating',
            expires_at=expires_at,
        )
        db.session.add(instance)
        safe_commit()
        return instance

    @staticmethod
    def update(instance_id, **kwargs):
        instance = ChallengeInstance.query.get(instance_id)
        if not instance:
            return None
        for k, v in kwargs.items():
            setattr(instance, k, v)
        safe_commit()
        return instance

    @staticmethod
    def mark_stopped(instance_id):
        instance = ChallengeInstance.query.get(instance_id)
        if instance:
            instance.status = 'stopped'
            instance.stopped_at = datetime.datetime.utcnow()
            safe_commit()
        return instance

    @staticmethod
    def mark_destroyed(instance_id):
        instance = ChallengeInstance.query.get(instance_id)
        if instance:
            instance.status = 'destroyed'
            instance.stopped_at = datetime.datetime.utcnow()
            safe_commit()
        return instance

    # ------------------------------------------------------------------ #
    #  ContainerLog queries
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_log(instance_id, message, level='info'):
        log = ContainerLog(instance_id=instance_id, message=message, level=level)
        db.session.add(log)
        safe_commit()
        return log

    @staticmethod
    def get_logs(instance_id, limit=200):
        return (
            ContainerLog.query
            .filter_by(instance_id=instance_id)
            .order_by(ContainerLog.timestamp.asc())
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------ #
    #  InstanceSnapshot queries
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_snapshot(instance_id, snapshot_name, image_ref=None):
        snap = InstanceSnapshot(
            instance_id=instance_id,
            snapshot_name=snapshot_name,
            image_ref=image_ref,
        )
        db.session.add(snap)
        safe_commit()
        return snap

    @staticmethod
    def get_snapshots(instance_id):
        return (
            InstanceSnapshot.query
            .filter_by(instance_id=instance_id)
            .order_by(InstanceSnapshot.created_at.asc())
            .all()
        )
