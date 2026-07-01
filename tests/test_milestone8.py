import json
import datetime
from unittest.mock import patch
import pytest

from app.extensions import db
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.docker_image_repository import DockerImageRepository
from app.repositories.deployment_profile_repository import DeploymentProfileRepository
from app.repositories.challenge_instance_repository import ChallengeInstanceRepository
from app.services.docker_service import DockerService
from app.services.instance_service import InstanceService
from app.services.auth_service import hash_password


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_roles_and_perms(app):
    with app.app_context():
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()


@pytest.fixture
def admin_user_id(app):
    with app.app_context():
        user = UserRepository.get_by_name('admin')
        if not user:
            user = UserRepository.create(
                username='admin',
                password_hash=hash_password('adminpass'),
                display_name='Admin User',
                role_name='Admin'
            )
        return user.id


@pytest.fixture
def participant_user_id(app):
    with app.app_context():
        user = UserRepository.get_by_name('participant')
        if not user:
            user = UserRepository.create(
                username='participant',
                password_hash=hash_password('userpass'),
                display_name='Participant User',
                role_name='Participant'
            )
        return user.id


# ---------------------------------------------------------------------------
# Test Core Repositories & Services
# ---------------------------------------------------------------------------

def test_docker_service_simulation(app):
    with app.app_context():
        # Force simulation mode for tests if docker daemon isn't guaranteed
        with patch('app.services.docker_service._DOCKER_AVAILABLE', False):
            assert DockerService.mode() == 'simulated'

            # Test pulling
            ok, msg = DockerService.pull_image('test-image:latest')
            assert ok
            assert 'simulated' in msg

            # Test running
            ok, cid, port, msg = DockerService.run_container(
                'test-image:latest',
                container_port=80,
                cpu_limit=0.5,
                memory_limit='64m'
            )
            assert ok
            assert cid is not None
            assert port >= 10000

            # Test status
            status = DockerService.container_status(cid)
            assert status is not None
            assert status['running'] is True

            # Test stop
            ok, msg = DockerService.stop_container(cid)
            assert ok
            status = DockerService.container_status(cid)
            assert status['running'] is False

            # Test remove
            ok, msg = DockerService.remove_container(cid)
            assert ok
            assert DockerService.container_status(cid) is None


def test_docker_image_repository(app):
    with app.app_context():
        img = DockerImageRepository.create(
            name='pwn-challenge',
            tag='v1.0',
            registry='ghcr.io/test',
            description='A pwn challenge',
            size_bytes=1024000
        )
        assert img.id is not None
        assert img.full_ref == 'ghcr.io/test/pwn-challenge:v1.0'

        # Fetch
        fetched = DockerImageRepository.get_by_id(img.id)
        assert fetched.name == 'pwn-challenge'

        fetched2 = DockerImageRepository.get_by_name_tag('pwn-challenge', 'v1.0')
        assert fetched2.id == img.id

        # Update
        updated = DockerImageRepository.update(img.id, tag='v1.1')
        assert updated.tag == 'v1.1'
        assert updated.full_ref == 'ghcr.io/test/pwn-challenge:v1.1'

        # Delete
        DockerImageRepository.delete(img.id)
        assert DockerImageRepository.get_by_id(img.id) is None


def test_deployment_profile_repository(app):
    with app.app_context():
        profile = DeploymentProfileRepository.create(
            name='standard-pwn',
            cpu_limit=0.25,
            memory_limit='256m',
            ttl_minutes=45,
            max_instances_per_user=2
        )
        assert profile.id is not None

        # Fetch
        fetched = DeploymentProfileRepository.get_by_id(profile.id)
        assert fetched.name == 'standard-pwn'
        assert fetched.cpu_limit == 0.25

        # Update
        updated = DeploymentProfileRepository.update(profile.id, pids_limit=128)
        assert updated.pids_limit == 128

        # Delete
        DeploymentProfileRepository.delete(profile.id)
        assert DeploymentProfileRepository.get_by_id(profile.id) is None


def test_challenge_instance_repository_and_logs(app, participant_user_id):
    with app.app_context():
        # Create an instance
        inst = ChallengeInstanceRepository.create(
            challenge_id=42,
            docker_image_id=1,
            user_id=participant_user_id,
            ttl_minutes=20
        )
        assert inst.id is not None
        assert inst.status == 'creating'
        assert inst.expires_at > datetime.datetime.utcnow()

        # Update
        ChallengeInstanceRepository.update(inst.id, status='running', mapped_port=12345)
        inst = ChallengeInstanceRepository.get_by_id(inst.id)
        assert inst.status == 'running'
        assert inst.mapped_port == 12345

        # Add Logs
        ChallengeInstanceRepository.add_log(inst.id, 'Container started.', level='info')
        ChallengeInstanceRepository.add_log(inst.id, 'Warning detected.', level='warn')

        logs = ChallengeInstanceRepository.get_logs(inst.id)
        assert len(logs) == 2
        assert logs[0].message == 'Container started.'
        assert logs[1].level == 'warn'

        # Add Snapshots
        snap = ChallengeInstanceRepository.add_snapshot(inst.id, 'snap-1', image_ref='snap-img-ref')
        assert snap.id is not None
        snaps = ChallengeInstanceRepository.get_snapshots(inst.id)
        assert len(snaps) == 1
        assert snaps[0].snapshot_name == 'snap-1'

        # Mark stopped/destroyed
        ChallengeInstanceRepository.mark_stopped(inst.id)
        assert inst.status == 'stopped'

        ChallengeInstanceRepository.mark_destroyed(inst.id)
        assert inst.status == 'destroyed'


def test_instance_service_lifecycle_simulation(app, participant_user_id):
    with app.app_context():
        # Ensure simulated mode
        with patch('app.services.docker_service._DOCKER_AVAILABLE', False):
            # Create a test DockerImage
            img = DockerImageRepository.create(
                name='web-easy',
                tag='latest',
                registry=None
            )

            # Launch
            ok, inst, msg = InstanceService.launch(
                challenge_id=99,
                docker_image_id=img.id,
                user_id=participant_user_id,
                container_port=80
            )
            assert ok
            assert inst.status == 'running'
            assert inst.mapped_port is not None
            assert inst.container_id is not None

            # Check status
            status = InstanceService.status(inst.id)
            assert status['status'] == 'running'
            assert status['mapped_port'] == inst.mapped_port

            # Stop
            ok, msg = InstanceService.stop(inst.id)
            assert ok
            assert ChallengeInstanceRepository.get_by_id(inst.id).status == 'stopped'

            # Destroy
            ok, msg = InstanceService.destroy(inst.id)
            assert ok
            assert ChallengeInstanceRepository.get_by_id(inst.id).status == 'destroyed'


# ---------------------------------------------------------------------------
# Test REST Routes (User & Admin)
# ---------------------------------------------------------------------------

def test_docker_routes_auth_required(client):
    # Try unauthorized endpoints
    res = client.post('/docker/instances/launch', json={})
    assert res.status_code in (302, 401)


def test_user_lifecycle_endpoints(app, client, participant_user_id):
    # Disable CSRF for testing
    app.config['WTF_CSRF_ENABLED'] = False

    # Log in user
    client.post('/login', data={'username': 'participant', 'password': 'userpass'})

    with app.app_context():
        img = DockerImageRepository.create(name='pwn-chal', tag='latest')
        img_id = img.id

    with patch('app.services.docker_service._DOCKER_AVAILABLE', False):
        # 1. Launch
        res = client.post('/docker/instances/launch', json={
            'challenge_id': 101,
            'docker_image_id': img_id,
            'container_port': 8080
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['ok'] is True
        inst_id = data['instance']['id']
        assert data['instance']['status'] == 'running'

        # 2. Status
        res = client.get(f'/docker/instances/{inst_id}/status')
        assert res.status_code == 200
        assert res.get_json()['instance']['status'] == 'running'

        # 3. Logs
        res = client.get(f'/docker/instances/{inst_id}/logs')
        assert res.status_code == 200
        assert 'logs' in res.get_json()

        # 4. Stop
        res = client.post(f'/docker/instances/{inst_id}/stop')
        assert res.status_code == 200

        # 5. Destroy
        res = client.post(f'/docker/instances/{inst_id}/destroy')
        assert res.status_code == 200


def test_admin_only_endpoints(app, client, admin_user_id, participant_user_id):
    app.config['WTF_CSRF_ENABLED'] = False

    # Log in participant first
    client.post('/login', data={'username': 'participant', 'password': 'userpass'})

    # Check that participant is forbidden from admin endpoints
    res = client.get('/admin/docker/images')
    assert res.status_code in (302, 403)

    # Now log in admin
    client.post('/admin/login', data={'username': 'admin', 'password': 'adminpass'})

    # Create Docker Image via Admin API
    res = client.post('/admin/docker/images', json={
        'name': 'admin-challenge',
        'tag': 'v2',
        'description': 'Created via admin endpoint'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['ok'] is True
    image_id = data['id']

    # Get Single Image
    res = client.get(f'/admin/docker/images/{image_id}')
    assert res.status_code == 200
    assert res.get_json()['name'] == 'admin-challenge'

    # List Images
    res = client.get('/admin/docker/images')
    assert res.status_code == 200
    assert len(res.get_json()) >= 1

    # Create Deployment Profile
    res = client.post('/admin/docker/profiles', json={
        'name': 'admin-profile',
        'cpu_limit': 1.0,
        'memory_limit': '512m',
        'ttl_minutes': 60
    })
    assert res.status_code == 201
    profile_id = res.get_json()['id']

    # List Profiles
    res = client.get('/admin/docker/profiles')
    assert res.status_code == 200
    assert len(res.get_json()) >= 1

    # Update Profile
    res = client.patch(f'/admin/docker/profiles/{profile_id}', json={'ttl_minutes': 120})
    assert res.status_code == 200

    # Delete Image & Profile
    res = client.delete(f'/admin/docker/images/{image_id}')
    assert res.status_code == 200

    res = client.delete(f'/admin/docker/profiles/{profile_id}')
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# Test CLI Commands
# ---------------------------------------------------------------------------

def test_docker_cli_commands(app):
    runner = app.test_cli_runner()

    # 1. Test docker-mode
    result = runner.invoke(args=['docker-mode'])
    assert result.exit_code == 0
    assert '[DockerService] mode =' in result.output

    # 2. Test docker-image-add
    result = runner.invoke(args=['docker-image-add', 'cli-chal', '--tag', 'v1', '--description', 'CLI added'])
    assert result.exit_code == 0
    assert '[OK] Registered image' in result.output

    # 3. Test docker-image-list
    result = runner.invoke(args=['docker-image-list'])
    assert result.exit_code == 0
    assert 'cli-chal:v1' in result.output

    # 4. Test docker-profile-add
    result = runner.invoke(args=['docker-profile-add', 'cli-profile', '--cpu', '0.5', '--memory', '128m'])
    assert result.exit_code == 0
    assert '[OK] Created profile' in result.output

    # 5. Test docker-reap
    result = runner.invoke(args=['docker-reap'])
    assert result.exit_code == 0
    assert 'Reaped' in result.output
