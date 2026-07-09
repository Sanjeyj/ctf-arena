"""
Unit and Integration tests for Policy Conflict Detection.
Phase 38 — Adaptive Policy Optimization & Governance Fabric.
Contains 10 test cases covering PolicyConflict model, detection logic, resolution, and REST endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.control_policy import ControlPolicy
from app.models.policy_conflict import PolicyConflict
from app.services.policy_conflict_service import PolicyConflictService
from app.research.routes import create_jwt


@pytest.fixture
def pc_setup(app):
    with app.app_context():
        db.session.query(PolicyConflict).delete()
        db.session.query(ControlPolicy).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="PC Org", slug="pc-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        p1 = ControlPolicy(
            policy_name="Firewall Policy A",
            policy_type="network",
            enforcement_mode="observe",
            rule_json=json.dumps({"max_ports": 100, "allow_outbound": True}),
            status="active",
            organization_id=org.id
        )
        p2 = ControlPolicy(
            policy_name="Firewall Policy B",
            policy_type="network",
            enforcement_mode="deny_simulation",
            rule_json=json.dumps({"max_ports": 50, "allow_outbound": False}),
            status="active",
            organization_id=org.id
        )
        db.session.add_all([p1, p2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "p1": p1,
            "p2": p2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_policy_conflict_model(app, pc_setup):
    """Test 1: PolicyConflict model basic persistence."""
    with app.app_context():
        conflict = PolicyConflict(
            source_policy_id=pc_setup["p1"].id,
            target_policy_id=pc_setup["p2"].id,
            conflict_type="contradiction",
            severity="high",
            description="Test conflict",
            confidence_score=85.0,
            status="open",
            organization_id=pc_setup["org"].id
        )
        db.session.add(conflict)
        db.session.commit()
        assert conflict.id is not None
        assert conflict.conflict_type == "contradiction"


def test_compare_rules_contradiction(app, pc_setup):
    """Test 2: compare_rules detects contradictions on shared rule keys."""
    with app.app_context():
        p1 = pc_setup["p1"]
        p2 = pc_setup["p2"]
        result = PolicyConflictService.compare_rules(p1, p2)
        assert result is not None
        assert result["type"] in ("contradiction", "enforcement_conflict")


def test_detect_conflicts_creates_records(app, pc_setup):
    """Test 3: detect_conflicts returns conflict records for contradicting policies."""
    with app.app_context():
        conflicts = PolicyConflictService.detect_conflicts(pc_setup["org"].id)
        assert len(conflicts) >= 1


def test_classify_conflict(app, pc_setup):
    """Test 4: classify_conflict returns the conflict type string."""
    with app.app_context():
        conflicts = PolicyConflictService.detect_conflicts(pc_setup["org"].id)
        if conflicts:
            ct = PolicyConflictService.classify_conflict(conflicts[0].id, pc_setup["org"].id)
            assert ct in ("contradiction", "enforcement_conflict", "scope_overlap")


def test_calculate_confidence(app, pc_setup):
    """Test 5: calculate_confidence returns a positive confidence score."""
    with app.app_context():
        conflicts = PolicyConflictService.detect_conflicts(pc_setup["org"].id)
        if conflicts:
            score = PolicyConflictService.calculate_confidence(conflicts[0].id, pc_setup["org"].id)
            assert score > 0.0


def test_recommend_resolution(app, pc_setup):
    """Test 6: recommend_resolution returns a non-empty recommendation string."""
    with app.app_context():
        conflicts = PolicyConflictService.detect_conflicts(pc_setup["org"].id)
        if conflicts:
            rec = PolicyConflictService.recommend_resolution(conflicts[0].id, pc_setup["org"].id)
            assert rec is not None
            assert len(rec) > 0


def test_resolve_conflict_valid(app, pc_setup):
    """Test 7: resolve_conflict transitions status to 'resolved'."""
    with app.app_context():
        conflicts = PolicyConflictService.detect_conflicts(pc_setup["org"].id)
        if conflicts:
            resolved = PolicyConflictService.resolve_conflict(conflicts[0].id, "resolved", pc_setup["org"].id)
            assert resolved.status == "resolved"


def test_resolve_conflict_invalid_status(app, pc_setup):
    """Test 8: resolve_conflict raises ValueError for invalid status values."""
    with app.app_context():
        conflicts = PolicyConflictService.detect_conflicts(pc_setup["org"].id)
        if conflicts:
            with pytest.raises(ValueError, match="Invalid status"):
                PolicyConflictService.resolve_conflict(conflicts[0].id, "bad_status", pc_setup["org"].id)


def test_conflict_summary(app, pc_setup):
    """Test 9: conflict_summary returns total, open, and critical counts."""
    with app.app_context():
        PolicyConflictService.detect_conflicts(pc_setup["org"].id)
        summary = PolicyConflictService.conflict_summary(pc_setup["org"].id)
        assert "total_conflicts" in summary
        assert "open_conflicts" in summary
        assert "critical_conflicts" in summary


def test_api_get_conflicts_endpoint(app, client, pc_setup):
    """Test 10: GET /api/v1/governance-intelligence/conflicts returns 200."""
    response = client.get(
        f"/api/v1/governance-intelligence/conflicts?org_id={pc_setup['org'].id}",
        headers=pc_setup["headers"]
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
