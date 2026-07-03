"""
Unit and Integration tests for Phase 28 Cyber Civilization Platform — Innovation.
Contains 12 test cases covering R&D projects, tracking, timeline forecasts, priorities, and APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.innovation_project import InnovationProject
from app.services.innovation_service import InnovationService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def inn_setup(app):
    """Fixture for innovation tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(InnovationProject).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Innovation Org", slug="innovation-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="inn_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Inn Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "inn_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_innovation_project_creation(app, inn_setup):
    """Test 1: InnovationProject model fields."""
    with app.app_context():
        project = InnovationProject(
            title="Quantum-Safe Cryptography",
            category="Crypto",
            progress=0.35,
            owner="Dr. Smith",
            organization_id=inn_setup["org"].id
        )
        db.session.add(project)
        db.session.commit()
        assert project.id is not None
        assert project.title == "Quantum-Safe Cryptography"
        assert project.category == "Crypto"
        assert project.progress == 0.35


def test_innovation_project_to_dict(app, inn_setup):
    """Test 2: InnovationProject serialization."""
    with app.app_context():
        project = InnovationProject(
            title="AI Threat Hunter",
            category="AI",
            progress=0.72,
            owner="Dr. Lee",
            organization_id=inn_setup["org"].id
        )
        db.session.add(project)
        db.session.commit()
        d = project.to_dict()
        assert d["title"] == "AI Threat Hunter"
        assert d["category"] == "AI"
        assert d["progress"] == 0.72
        assert d["owner"] == "Dr. Lee"


def test_innovation_service_track_progress(app, inn_setup):
    """Test 3: Track function increments project progress correctly."""
    with app.app_context():
        project = InnovationProject(title="P1", category="AI", progress=0.4, owner="O1", organization_id=inn_setup["org"].id)
        db.session.add(project)
        db.session.commit()

        result = InnovationService.track(project.id, progress_delta=0.2)
        assert result.progress == 0.6


def test_innovation_service_track_clamps_max(app, inn_setup):
    """Test 4: Track function clamps at 1.0 maximum boundary."""
    with app.app_context():
        project = InnovationProject(title="P2", category="OS", progress=0.9, owner="O2", organization_id=inn_setup["org"].id)
        db.session.add(project)
        db.session.commit()

        result = InnovationService.track(project.id, progress_delta=0.5)
        assert result.progress == 1.0


def test_innovation_service_track_clamps_min(app, inn_setup):
    """Test 5: Track function clamps at 0.0 minimum boundary."""
    with app.app_context():
        project = InnovationProject(title="P3", category="Hardware", progress=0.1, owner="O3", organization_id=inn_setup["org"].id)
        db.session.add(project)
        db.session.commit()

        result = InnovationService.track(project.id, progress_delta=-0.5)
        assert result.progress == 0.0


def test_innovation_service_track_not_found(app):
    """Test 6: Track returns None for non-existent project ID."""
    with app.app_context():
        result = InnovationService.track(99999, progress_delta=0.1)
        assert result is None


def test_innovation_service_forecast_timeline(app, inn_setup):
    """Test 7: Forecast returns remaining timeline estimate in months."""
    with app.app_context():
        project = InnovationProject(title="P4", category="Network", progress=0.5, owner="O4", organization_id=inn_setup["org"].id)
        db.session.add(project)
        db.session.commit()

        months = InnovationService.forecast(project.id)
        assert months == 6.0  # (1.0 - 0.5) * 12.0


def test_innovation_service_forecast_complete(app, inn_setup):
    """Test 8: Forecast returns 0 months when project is fully complete."""
    with app.app_context():
        project = InnovationProject(title="P5", category="AI", progress=1.0, owner="O5", organization_id=inn_setup["org"].id)
        db.session.add(project)
        db.session.commit()

        months = InnovationService.forecast(project.id)
        assert months == 0.0


def test_innovation_service_forecast_not_found(app):
    """Test 9: Forecast returns 999.9 for missing project ID."""
    with app.app_context():
        months = InnovationService.forecast(99999)
        assert months == 999.9


def test_innovation_service_prioritize_sort_order(app, inn_setup):
    """Test 10: Prioritize lists projects sorted by ascending progress."""
    with app.app_context():
        p1 = InnovationProject(title="High Progress", category="AI", progress=0.9, owner="O1", organization_id=inn_setup["org"].id)
        p2 = InnovationProject(title="Low Progress", category="AI", progress=0.2, owner="O2", organization_id=inn_setup["org"].id)
        p3 = InnovationProject(title="Mid Progress", category="AI", progress=0.5, owner="O3", organization_id=inn_setup["org"].id)
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        prioritized = InnovationService.prioritize(org_id=inn_setup["org"].id)
        assert prioritized[0].title == "Low Progress"
        assert prioritized[1].title == "Mid Progress"
        assert prioritized[2].title == "High Progress"


def test_innovation_service_prioritize_empty(app, inn_setup):
    """Test 11: Prioritize returns empty list when no projects exist."""
    with app.app_context():
        result = InnovationService.prioritize(org_id=inn_setup["org"].id)
        assert result == []


def test_api_get_innovation(client, inn_setup):
    """Test 12: GET /api/v1/innovation REST endpoint."""
    with client.application.app_context():
        project = InnovationProject(
            title="API Project",
            category="Network",
            progress=0.65,
            owner="API Owner",
            organization_id=inn_setup["org"].id
        )
        db.session.add(project)
        db.session.commit()

    resp = client.get(
        f'/api/v1/innovation?org_id={inn_setup["org"].id}',
        headers=inn_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["title"] == "API Project"
