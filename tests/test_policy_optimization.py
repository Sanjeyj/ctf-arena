"""
Unit and Integration tests for Policy Optimization Runs.
Phase 38 — Adaptive Policy Optimization & Governance Fabric.
Contains 10 test cases covering PolicyOptimizationRun model, service runs, comparisons, and REST endpoints.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.control_policy import ControlPolicy
from app.models.policy_optimization_run import PolicyOptimizationRun
from app.services.policy_optimization_service import PolicyOptimizationService
from app.research.routes import create_jwt


@pytest.fixture
def po_setup(app):
    with app.app_context():
        db.session.query(PolicyOptimizationRun).delete()
        db.session.query(ControlPolicy).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="PO Org", slug="po-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        policy = ControlPolicy(
            policy_name="Network Access Policy",
            policy_type="network",
            enforcement_mode="observe",
            rule_json='{"max_connections": 100}',
            status="active",
            organization_id=org.id
        )
        db.session.add(policy)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "org": org,
            "policy": policy,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_policy_optimization_run_model(app, po_setup):
    """Test 1: PolicyOptimizationRun model persists correctly."""
    with app.app_context():
        run = PolicyOptimizationRun(
            policy_id=po_setup["policy"].id,
            optimization_type="threshold_tuning",
            baseline_score=40.0,
            optimized_score=60.0,
            risk_before=60.0,
            risk_after=40.0,
            status="completed",
            organization_id=po_setup["org"].id
        )
        db.session.add(run)
        db.session.commit()
        assert run.id is not None
        assert run.optimized_score == 60.0


def test_create_run_service(app, po_setup):
    """Test 2: PolicyOptimizationService.create_run creates a pending run."""
    with app.app_context():
        run = PolicyOptimizationService.create_run(
            po_setup["policy"].id, "threshold_tuning", 42, po_setup["org"].id
        )
        assert run.id is not None
        assert run.status == "pending"
        assert run.policy_id == po_setup["policy"].id


def test_create_run_unknown_policy(app, po_setup):
    """Test 3: create_run raises ValueError for non-existent policy."""
    with app.app_context():
        with pytest.raises(ValueError, match="ControlPolicy not found"):
            PolicyOptimizationService.create_run(99999, "threshold_tuning", 0, po_setup["org"].id)


def test_simulate_adjustment(app, po_setup):
    """Test 4: simulate_adjustment completes the run and improves the score."""
    with app.app_context():
        run = PolicyOptimizationService.create_run(
            po_setup["policy"].id, "parameter_search", 123, po_setup["org"].id
        )
        result = PolicyOptimizationService.simulate_adjustment(run.id, po_setup["org"].id)
        assert result.status == "completed"
        assert result.optimized_score >= result.baseline_score


def test_calculate_improvement(app, po_setup):
    """Test 5: calculate_improvement returns non-negative gain."""
    with app.app_context():
        run = PolicyOptimizationService.create_run(
            po_setup["policy"].id, "threshold_tuning", 7, po_setup["org"].id
        )
        PolicyOptimizationService.simulate_adjustment(run.id, po_setup["org"].id)
        run_fresh = PolicyOptimizationRun.query.get(run.id)
        gain = PolicyOptimizationService.calculate_improvement(run_fresh)
        assert gain >= 0.0


def test_validate_constraints_pass(app, po_setup):
    """Test 6: validate_constraints returns True when risk is within limits."""
    with app.app_context():
        run = PolicyOptimizationService.create_run(
            po_setup["policy"].id, "threshold_tuning", 99, po_setup["org"].id
        )
        PolicyOptimizationService.simulate_adjustment(run.id, po_setup["org"].id)
        import json
        result = PolicyOptimizationService.validate_constraints(
            run.id, json.dumps({"max_acceptable_risk": 100.0}), po_setup["org"].id
        )
        assert result is True


def test_recommend_adjustment(app, po_setup):
    """Test 7: recommend_adjustment returns a non-empty dict after simulation."""
    with app.app_context():
        run = PolicyOptimizationService.create_run(
            po_setup["policy"].id, "threshold_tuning", 55, po_setup["org"].id
        )
        PolicyOptimizationService.simulate_adjustment(run.id, po_setup["org"].id)
        rec = PolicyOptimizationService.recommend_adjustment(run.id, po_setup["org"].id)
        assert isinstance(rec, dict)
        assert len(rec) > 0


def test_compare_runs(app, po_setup):
    """Test 8: compare_runs returns score_diff between two runs."""
    with app.app_context():
        r1 = PolicyOptimizationService.create_run(po_setup["policy"].id, "threshold_tuning", 10, po_setup["org"].id)
        PolicyOptimizationService.simulate_adjustment(r1.id, po_setup["org"].id)
        r2 = PolicyOptimizationService.create_run(po_setup["policy"].id, "parameter_search", 20, po_setup["org"].id)
        PolicyOptimizationService.simulate_adjustment(r2.id, po_setup["org"].id)
        comparison = PolicyOptimizationService.compare_runs(r1.id, r2.id, po_setup["org"].id)
        assert "score_diff" in comparison


def test_optimization_summary(app, po_setup):
    """Test 9: optimization_summary returns correct aggregate fields."""
    with app.app_context():
        run = PolicyOptimizationService.create_run(po_setup["policy"].id, "threshold_tuning", 33, po_setup["org"].id)
        PolicyOptimizationService.simulate_adjustment(run.id, po_setup["org"].id)
        summary = PolicyOptimizationService.optimization_summary(po_setup["org"].id)
        assert summary["total_runs"] >= 1
        assert "average_improvement" in summary


def test_api_optimize_policy_endpoint(app, client, po_setup):
    """Test 10: POST /api/v1/governance-intelligence/policies/<id>/optimize returns 200."""
    response = client.post(
        f"/api/v1/governance-intelligence/policies/{po_setup['policy'].id}/optimize",
        json={"org_id": po_setup["org"].id, "optimization_type": "threshold_tuning", "random_seed": 42},
        headers=po_setup["headers"]
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "completed"
