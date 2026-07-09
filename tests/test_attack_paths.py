"""
Unit and Integration tests for AttackPathService.
Contains 10 test cases covering graph builders, path calculations, cycle protections, critical paths, path comparisons, and hooks.
"""
import pytest
import datetime
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.exposure_asset import ExposureAsset
from app.models.architecture_zone import ArchitectureZone
from app.models.attack_path import AttackPath
from app.models.universe_link import UniverseLink
from app.services.architecture_service import ArchitectureService
from app.services.attack_path_service import AttackPathService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def path_setup(app):
    with app.app_context():
        db.session.query(UniverseLink).delete()
        db.session.query(AttackPath).delete()
        db.session.query(ExposureAsset).delete()
        db.session.query(ArchitectureZone).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        z_pub = ArchitectureService.create_zone("Public", "public", "pub", 0.1, "high", o1.id)
        z_edge = ArchitectureService.create_zone("Edge", "edge", "edge", 0.5, "medium", o1.id)
        z_app = ArchitectureService.create_zone("App", "application", "app", 0.9, "high", o1.id)

        a1 = ExposureAsset(asset_reference_type="asset", asset_reference_id=1, display_name="A1", architecture_zone_id=z_pub.id, organization_id=o1.id)
        a2 = ExposureAsset(asset_reference_type="asset", asset_reference_id=2, display_name="A2", architecture_zone_id=z_edge.id, organization_id=o1.id)
        a3 = ExposureAsset(asset_reference_type="asset", asset_reference_id=3, display_name="A3", architecture_zone_id=z_app.id, organization_id=o1.id)

        db.session.add_all([a1, a2, a3])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "z_pub": z_pub,
            "z_edge": z_edge,
            "z_app": z_app,
            "a1": a1,
            "a2": a2,
            "a3": a3,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_attack_path_model(app, path_setup):
    """Test 1: AttackPath model fields validation."""
    with app.app_context():
        ap = AttackPath(
            name="Path A1 to A3",
            source_asset_id=path_setup["a1"].id,
            target_asset_id=path_setup["a3"].id,
            path_json="[1, 2, 3]",
            hop_count=2,
            path_risk_score=15.0,
            organization_id=path_setup["o1"].id
        )
        db.session.add(ap)
        db.session.commit()
        assert ap.id is not None
        assert ap.name == "Path A1 to A3"


def test_build_graph_default_zones(app, path_setup):
    """Test 2: build_graph connects nodes across zones public -> edge -> application."""
    with app.app_context():
        adj = AttackPathService.build_graph(path_setup["o1"].id)
        assert path_setup["a2"].id in adj[path_setup["a1"].id]
        assert path_setup["a3"].id in adj[path_setup["a2"].id]


def test_calculate_paths(app, path_setup):
    """Test 3: calculate_paths finds route A1 -> A2 -> A3."""
    with app.app_context():
        paths = AttackPathService.calculate_paths(path_setup["a1"].id, path_setup["a3"].id, path_setup["o1"].id)
        assert len(paths) == 1
        assert paths[0] == [path_setup["a1"].id, path_setup["a2"].id, path_setup["a3"].id]


def test_calculate_paths_cycle_protection(app, path_setup):
    """Test 4: calculate_paths protects against graph cycles."""
    with app.app_context():
        # Create a loop: A1 -> A2, A2 -> A1 (normally we only have zone flow, let's inject UniverseLink manually to force cycle)
        from app.models.defense_universe import DefenseUniverse
        u = DefenseUniverse(name="Test Universe", organization_id=path_setup["o1"].id)
        db.session.add(u)
        db.session.commit()

        l1 = UniverseLink(universe_id=u.id, source_node_id=2, target_node_id=1, relationship_type="route", organization_id=path_setup["o1"].id)
        db.session.add(l1)
        db.session.commit()

        # Re-verify calculation finishes cleanly (no stack overflow)
        paths = AttackPathService.calculate_paths(path_setup["a1"].id, path_setup["a3"].id, path_setup["o1"].id)
        assert len(paths) >= 1


def test_score_path(app, path_setup):
    """Test 5: score_path sum of scores."""
    with app.app_context():
        score = AttackPathService.score_path([path_setup["a1"].id, path_setup["a2"].id], path_setup["o1"].id)
        # S1 (A1): public zone -> not internet_exposed -> base score 2.0
        # S2 (A2): edge zone -> not internet_exposed -> base score 2.0
        # Total: 4.0
        assert score == 4.0


def test_find_critical_path(app, path_setup):
    """Test 6: find_critical_path returns and saves AttackPath."""
    with app.app_context():
        ap = AttackPathService.find_critical_path(path_setup["a1"].id, path_setup["a3"].id, path_setup["o1"].id)
        assert ap is not None
        assert ap.hop_count == 2
        assert ap.path_risk_score == 6.0  # three internal assets: 2.0 * 3 = 6.0


def test_find_critical_path_hook_mutation(app, path_setup):
    """Test 7: before_attack_path_analysis hook risk mutation."""
    with app.app_context():
        HookService.clear_all()
        def callback(source_id, target_id, path, risk_score, org_id):
            return {'risk_score': 999.0}

        HookService.register_hook('before_attack_path_analysis', callback)
        ap = AttackPathService.find_critical_path(path_setup["a1"].id, path_setup["a3"].id, path_setup["o1"].id)
        assert ap.path_risk_score == 999.0
        HookService.clear_all()


def test_explain_path(app, path_setup):
    """Test 8: explain_path compiles detailed description."""
    with app.app_context():
        ap = AttackPathService.find_critical_path(path_setup["a1"].id, path_setup["a3"].id, path_setup["o1"].id)
        explanation = AttackPathService.explain_path(ap.id, path_setup["o1"].id)
        assert "hops" in explanation
        assert "A1 -> A2 -> A3" in explanation


def test_compare_paths(app, path_setup):
    """Test 9: compare_paths highlights risk delta."""
    with app.app_context():
        ap1 = AttackPathService.find_critical_path(path_setup["a1"].id, path_setup["a3"].id, path_setup["o1"].id)

        # Create another path manually with higher score
        ap2 = AttackPath(
            name="Path 2",
            source_asset_id=path_setup["a1"].id,
            target_asset_id=path_setup["a3"].id,
            path_json="[1, 3]",
            hop_count=1,
            path_risk_score=2.0,
            organization_id=path_setup["o1"].id
        )
        db.session.add(ap2)
        db.session.commit()

        comp = AttackPathService.compare_paths(ap1.id, ap2.id, path_setup["o1"].id)
        # ap1 (6.0) vs ap2 (2.0) -> delta 4.0 points higher
        assert "4.0 points higher" in comp


def test_attack_path_tenant_boundary(app, path_setup):
    """Test 10: Paths cannot be retrieved across tenant boundaries."""
    with app.app_context():
        ap = AttackPathService.find_critical_path(path_setup["a1"].id, path_setup["a3"].id, path_setup["o1"].id)

        # Query with wrong organization_id
        explanation = AttackPathService.explain_path(ap.id, 9999)
        assert explanation == "Path not found."
