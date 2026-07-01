"""
Docker blueprint — user-facing container lifecycle routes.

Routes
------
  POST   /docker/instances/launch          Launch a container for a challenge
  POST   /docker/instances/<id>/stop       Stop a running instance
  POST   /docker/instances/<id>/destroy    Destroy (stop + remove) an instance
  GET    /docker/instances/<id>/status     Get instance status + live Docker state
  GET    /docker/instances/<id>/logs       Get structured container logs
  GET    /docker/mode                      Report current Docker engine mode
"""

from flask import jsonify, request, g
from flask_login import login_required, current_user

from app.docker import docker_bp
from app.services.instance_service import InstanceService
from app.repositories.challenge_instance_repository import ChallengeInstanceRepository


# ---------------------------------------------------------------------------
# Engine mode
# ---------------------------------------------------------------------------

@docker_bp.route('/docker/mode', methods=['GET'])
def engine_mode():
    from app.services.docker_service import DockerService
    return jsonify({'mode': DockerService.mode(), 'ok': True})


# ---------------------------------------------------------------------------
# Instance lifecycle — user-facing
# ---------------------------------------------------------------------------

@docker_bp.route('/docker/instances/launch', methods=['POST'])
@login_required
def launch_instance():
    data = request.get_json(silent=True) or {}
    challenge_id = data.get('challenge_id')
    docker_image_id = data.get('docker_image_id')

    if not challenge_id or not docker_image_id:
        return jsonify({'ok': False, 'message': 'challenge_id and docker_image_id are required.'}), 400

    team_id = getattr(current_user, 'active_team_id', None)

    ok, instance, message = InstanceService.launch(
        challenge_id=int(challenge_id),
        docker_image_id=int(docker_image_id),
        user_id=current_user.id,
        team_id=team_id,
        deployment_profile_id=data.get('deployment_profile_id'),
        container_port=data.get('container_port'),
        env=data.get('env'),
    )

    if not ok:
        return jsonify({'ok': False, 'message': message}), 422

    return jsonify({
        'ok': True,
        'message': message,
        'instance': {
            'id': instance.id,
            'status': instance.status,
            'mapped_port': instance.mapped_port,
            'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
        },
    }), 201


@docker_bp.route('/docker/instances/<int:instance_id>/stop', methods=['POST'])
@login_required
def stop_instance(instance_id):
    instance = ChallengeInstanceRepository.get_by_id(instance_id)
    if not instance:
        return jsonify({'ok': False, 'message': 'Instance not found.'}), 404
    if instance.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'ok': False, 'message': 'Forbidden.'}), 403

    ok, message = InstanceService.stop(instance_id)
    return jsonify({'ok': ok, 'message': message}), (200 if ok else 500)


@docker_bp.route('/docker/instances/<int:instance_id>/destroy', methods=['POST'])
@login_required
def destroy_instance(instance_id):
    instance = ChallengeInstanceRepository.get_by_id(instance_id)
    if not instance:
        return jsonify({'ok': False, 'message': 'Instance not found.'}), 404
    if instance.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'ok': False, 'message': 'Forbidden.'}), 403

    ok, message = InstanceService.destroy(instance_id)
    return jsonify({'ok': ok, 'message': message}), (200 if ok else 500)


@docker_bp.route('/docker/instances/<int:instance_id>/status', methods=['GET'])
@login_required
def instance_status(instance_id):
    instance = ChallengeInstanceRepository.get_by_id(instance_id)
    if not instance:
        return jsonify({'ok': False, 'message': 'Instance not found.'}), 404
    if instance.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'ok': False, 'message': 'Forbidden.'}), 403

    data = InstanceService.status(instance_id)
    return jsonify({'ok': True, 'instance': data})


@docker_bp.route('/docker/instances/<int:instance_id>/logs', methods=['GET'])
@login_required
def instance_logs(instance_id):
    instance = ChallengeInstanceRepository.get_by_id(instance_id)
    if not instance:
        return jsonify({'ok': False, 'message': 'Instance not found.'}), 404
    if instance.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'ok': False, 'message': 'Forbidden.'}), 403

    logs = ChallengeInstanceRepository.get_logs(instance_id, limit=200)
    return jsonify({
        'ok': True,
        'logs': [
            {'timestamp': l.timestamp.isoformat(), 'level': l.level, 'message': l.message}
            for l in logs
        ],
    })
