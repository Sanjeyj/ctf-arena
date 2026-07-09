import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.business_process import BusinessProcess
from app.models.business_dependency_risk import BusinessDependencyRisk
from app.services.dependency_risk_service import DependencyRiskService
from app.research.routes import create_jwt


@pytest.fixture
def dep_setup(app):
    with app.app_context():
        db.session.query(BusinessDependencyRisk).delete()
        db.session.query(BusinessProcess).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        bp1 = BusinessProcess(name="Payment", criticality="critical", rto=2.0, organization_id=o1.id)
        bp2 = BusinessProcess(name="Billing", criticality="medium", rto=4.0, organization_id=o1.id)
        db.session.add_all([bp1, bp2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "bp1": bp1,
            "bp2": bp2,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_map_dependency_valid(app, dep_setup):
    """Test 1: Map valid business dependency."""
    with app.app_context():
        dep = DependencyRiskService.map_dependency(
            dep_setup["bp1"].id, "third_party_vendors", 42, "vendor", 60.0, dep_setup["o1"].id
        )
        assert dep.id is not None
        assert dep.status == "active"


def test_map_dependency_invalid_type(app, dep_setup):
    """Test 2: Invalid dependency type triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            DependencyRiskService.map_dependency(
                dep_setup["bp1"].id, "vendors", 42, "invalid_type", 60.0, dep_setup["o1"].id
            )


def test_calculate_concentration_risk(app, dep_setup):
    """Test 3: Computes concentration score based on sharing count."""
    with app.app_context():
        # Add dependency on same vendor reference to bp1 and bp2
        DependencyRiskService.map_dependency(dep_setup["bp1"].id, "vendors", 99, "vendor", 60.0, dep_setup["o1"].id)
        dep2 = DependencyRiskService.map_dependency(dep_setup["bp2"].id, "vendors", 99, "vendor", 60.0, dep_setup["o1"].id)
        # Should be 2 shared. score = 2 * 20.0 = 40.0
        assert dep2.concentration_risk_score == 40.0


def test_calculate_failure_impact(app, dep_setup):
    """Test 4: Failure impact computes average of criticality."""
    with app.app_context():
        # bp1 is critical (100.0), dep is 60.0. Average = 80.0
        dep = DependencyRiskService.map_dependency(
            dep_setup["bp1"].id, "vendors", 42, "vendor", 60.0, dep_setup["o1"].id
        )
        assert dep.failure_impact_score == 80.0


def test_calculate_recovery_dependency(app, dep_setup):
    """Test 5: Recovery dependency calculated from RTO."""
    with app.app_context():
        # bp1 rto = 2.0. score = 100 - 20 = 80.0
        dep = DependencyRiskService.map_dependency(
            dep_setup["bp1"].id, "vendors", 42, "vendor", 60.0, dep_setup["o1"].id
        )
        assert dep.recovery_dependency_score == 80.0


def test_find_single_points_of_failure(app, dep_setup):
    """Test 6: Find critical single points of failure."""
    with app.app_context():
        # bp1 is critical (100.0) -> dependency mapped will trigger spof since criticality >= 80.0
        DependencyRiskService.map_dependency(dep_setup["bp1"].id, "vendors", 42, "vendor", 80.0, dep_setup["o1"].id)
        spofs = DependencyRiskService.find_single_points_of_failure(dep_setup["o1"].id)
        assert len(spofs) == 1


def test_rank_critical_dependencies(app, dep_setup):
    """Test 7: Ranks dependencies by failure impact."""
    with app.app_context():
        DependencyRiskService.map_dependency(dep_setup["bp1"].id, "vendors", 42, "vendor", 80.0, dep_setup["o1"].id)
        DependencyRiskService.map_dependency(dep_setup["bp2"].id, "vendors", 43, "vendor", 40.0, dep_setup["o1"].id)
        ranked = DependencyRiskService.rank_critical_dependencies(dep_setup["o1"].id)
        assert ranked[0].failure_impact_score > ranked[1].failure_impact_score


def test_dependency_summary(app, dep_setup):
    """Test 8: Summary metrics correctly aggregate."""
    with app.app_context():
        DependencyRiskService.map_dependency(dep_setup["bp1"].id, "vendors", 42, "vendor", 80.0, dep_setup["o1"].id)
        summary = DependencyRiskService.dependency_summary(dep_setup["o1"].id)
        assert summary["total_dependencies"] == 1
        assert summary["spof_count"] == 1


def test_api_dependencies_endpoint(app, client, dep_setup):
    """Test 9: REST API list dependencies endpoint."""
    res = client.get(
        f'/api/v1/strategic-resilience/dependencies?org_id={dep_setup["o1"].id}',
        headers=dep_setup["headers"]
    )
    assert res.status_code == 200


def test_api_dependencies_missing_org(app, client, dep_setup):
    """Test 10: Missing org parameter returns 400."""
    res = client.get('/api/v1/strategic-resilience/dependencies', headers=dep_setup["headers"])
    assert res.status_code == 400
