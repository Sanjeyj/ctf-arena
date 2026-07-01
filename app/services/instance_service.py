"""
InstanceService
===============
High-level orchestration layer for containerised CTF challenges.

Responsibilities
----------------
- Enforce per-user / per-team instance limits from DeploymentProfile.
- Delegate all Docker operations to DockerService.
- Persist lifecycle state via ChallengeInstanceRepository.
- Emit ContainerLog entries for every meaningful event.
- Provide a ``reap_expired`` helper for the background janitor CLI command.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from app.repositories.challenge_instance_repository import ChallengeInstanceRepository
from app.repositories.docker_image_repository import DockerImageRepository
from app.repositories.deployment_profile_repository import DeploymentProfileRepository
from app.services.docker_service import DockerService

logger = logging.getLogger(__name__)


class InstanceService:

    # ------------------------------------------------------------------
    # Provision
    # ------------------------------------------------------------------

    @staticmethod
    def launch(
        challenge_id: int,
        docker_image_id: int,
        *,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        deployment_profile_id: Optional[int] = None,
        container_port: Optional[int] = None,
        env: Optional[dict] = None,
    ) -> Tuple[bool, Optional[object], str]:
        """
        Provision a new container instance for a challenge.

        Returns (ok, ChallengeInstance | None, message).
        """
        # 1. Resolve deployment profile
        profile = None
        if deployment_profile_id:
            profile = DeploymentProfileRepository.get_by_id(deployment_profile_id)
        if profile is None:
            # Provide a sensible default without hitting the DB
            class _DefaultProfile:
                cpu_limit = 0.5
                memory_limit = '128m'
                pids_limit = 64
                network_disabled = False
                ttl_minutes = 30
                max_instances_per_user = 1
            profile = _DefaultProfile()

        # 2. Enforce instance limits
        if user_id:
            active = ChallengeInstanceRepository.count_active_for_user(user_id)
            if active >= profile.max_instances_per_user:
                return False, None, f'Instance limit reached ({profile.max_instances_per_user} max per user).'

        # 3. Resolve Docker image
        img = DockerImageRepository.get_by_id(docker_image_id)
        if not img:
            return False, None, f'Docker image #{docker_image_id} not found.'

        image_ref = img.full_ref  # e.g. 'ghcr.io/org/pwn:latest'

        # 4. Create DB record (status='creating')
        instance = ChallengeInstanceRepository.create(
            challenge_id=challenge_id,
            docker_image_id=docker_image_id,
            user_id=user_id,
            team_id=team_id,
            deployment_profile_id=getattr(profile, 'id', None),
            ttl_minutes=profile.ttl_minutes,
        )
        ChallengeInstanceRepository.add_log(instance.id, f'Provisioning image {image_ref}.')

        # 5. Pull image if not already local
        if not DockerService.image_exists(image_ref):
            ok, msg = DockerService.pull_image(image_ref)
            ChallengeInstanceRepository.add_log(instance.id, f'Pull: {msg}', level='info' if ok else 'error')
            if not ok:
                ChallengeInstanceRepository.update(instance.id, status='error')
                return False, instance, f'Failed to pull image: {msg}'

        # 6. Run container
        container_name = f'ctf_chal_{challenge_id}_inst_{instance.id}'
        ok, container_id, host_port, msg = DockerService.run_container(
            image_ref,
            container_name=container_name,
            container_port=container_port,
            env=env,
            cpu_limit=profile.cpu_limit,
            memory_limit=profile.memory_limit,
            pids_limit=profile.pids_limit,
            network_disabled=profile.network_disabled,
        )

        if not ok:
            ChallengeInstanceRepository.update(instance.id, status='error')
            ChallengeInstanceRepository.add_log(instance.id, f'Run failed: {msg}', level='error')
            return False, instance, f'Failed to start container: {msg}'

        import datetime
        ChallengeInstanceRepository.update(
            instance.id,
            container_id=container_id,
            mapped_port=host_port,
            status='running',
            started_at=datetime.datetime.utcnow(),
        )
        ChallengeInstanceRepository.add_log(instance.id, f'Container {container_id[:12]} running on port {host_port}.')
        logger.info('[InstanceService] Instance %d launched container %s', instance.id, container_id[:12])
        return True, instance, 'Instance started successfully.'

    # ------------------------------------------------------------------
    # Stop
    # ------------------------------------------------------------------

    @staticmethod
    def stop(instance_id: int) -> Tuple[bool, str]:
        """Stop (but do not remove) a running container."""
        instance = ChallengeInstanceRepository.get_by_id(instance_id)
        if not instance:
            return False, 'Instance not found.'
        if not instance.container_id:
            ChallengeInstanceRepository.mark_stopped(instance_id)
            return True, 'Instance marked stopped (no container_id).'

        ok, msg = DockerService.stop_container(instance.container_id)
        ChallengeInstanceRepository.add_log(instance_id, f'Stop: {msg}', level='info' if ok else 'warn')
        if ok:
            ChallengeInstanceRepository.mark_stopped(instance_id)
        return ok, msg

    # ------------------------------------------------------------------
    # Destroy
    # ------------------------------------------------------------------

    @staticmethod
    def destroy(instance_id: int) -> Tuple[bool, str]:
        """Stop and remove a container; mark the DB record as 'destroyed'."""
        instance = ChallengeInstanceRepository.get_by_id(instance_id)
        if not instance:
            return False, 'Instance not found.'

        if instance.container_id:
            ok, msg = DockerService.remove_container(instance.container_id)
            ChallengeInstanceRepository.add_log(instance_id, f'Remove: {msg}', level='info' if ok else 'warn')

        ChallengeInstanceRepository.mark_destroyed(instance_id)
        logger.info('[InstanceService] Instance %d destroyed.', instance_id)
        return True, 'Instance destroyed.'

    # ------------------------------------------------------------------
    # Reap expired
    # ------------------------------------------------------------------

    @staticmethod
    def reap_expired() -> int:
        """Destroy all instances that have passed their expiry time. Returns count reaped."""
        expired = ChallengeInstanceRepository.get_expired()
        reaped = 0
        for inst in expired:
            ok, msg = InstanceService.destroy(inst.id)
            if ok:
                reaped += 1
                logger.info('[InstanceService] Reaped expired instance %d.', inst.id)
            else:
                logger.warning('[InstanceService] Failed to reap instance %d: %s', inst.id, msg)
        return reaped

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @staticmethod
    def status(instance_id: int) -> Optional[dict]:
        """Return a dict with instance details and live Docker status."""
        instance = ChallengeInstanceRepository.get_by_id(instance_id)
        if not instance:
            return None
        docker_status = None
        if instance.container_id:
            docker_status = DockerService.container_status(instance.container_id)
        return {
            'id': instance.id,
            'challenge_id': instance.challenge_id,
            'user_id': instance.user_id,
            'team_id': instance.team_id,
            'container_id': instance.container_id,
            'ip_address': instance.ip_address,
            'mapped_port': instance.mapped_port,
            'status': instance.status,
            'started_at': instance.started_at.isoformat() if instance.started_at else None,
            'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
            'docker': docker_status,
        }
