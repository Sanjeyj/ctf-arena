import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_treatment_option import RiskTreatmentOption
from app.services.risk_treatment_service import RiskTreatmentService


@pytest.fixture
def treat_setup(app):
    with app.app_context():
        db.session.query(RiskTreatmentOption).delete()
        db.session.query(QuantitativeRiskScenario).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        s1 = QuantitativeRiskScenario(
            name="Ransomware Scenario", scenario_type="ransomware",
            inherent_risk_score=80.0, residual_risk_score=80.0, organization_id=o1.id
        )
        db.session.add(s1)
        db.session.commit()

        yield {"o1": o1, "s1": s1}


def test_create_option_valid(app, treat_setup):
    """Test 1: Create a valid treatment option updates DB."""
    with app.app_context():
        opt = RiskTreatmentService.create_option(
            treat_setup["s1"].id, "mitigate", "Backup System Isolation",
            "Isolate backup networks", 5000.0, 40.0, "medium", treat_setup["o1"].id
        )
        assert opt.id is not None
        assert opt.status == "proposed"


def test_create_option_invalid_type(app, treat_setup):
    """Test 2: Create option with invalid type triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            RiskTreatmentService.create_option(
                treat_setup["s1"].id, "invalid_type", "Backup Isolation",
                "Description", 5000.0, 40.0, "medium", treat_setup["o1"].id
            )


def test_create_option_invalid_reduction(app, treat_setup):
    """Test 3: Incorrect expected reduction bounds trigger ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            RiskTreatmentService.create_option(
                treat_setup["s1"].id, "mitigate", "Backup Isolation",
                "Description", 5000.0, 150.0, "medium", treat_setup["o1"].id
            )


def test_calculate_residual_risk(app, treat_setup):
    """Test 4: Correctly computes residual risk based on reduction pct."""
    with app.app_context():
        # Inherent: 80.0, reduction: 50% => residual = 40.0
        res = RiskTreatmentService.calculate_residual_risk(treat_setup["s1"].id, 50.0, treat_setup["o1"].id)
        assert res == 40.0


def test_calculate_residual_risk_zero(app, treat_setup):
    """Test 5: Residual risk with 0 reduction matches inherent risk."""
    with app.app_context():
        res = RiskTreatmentService.calculate_residual_risk(treat_setup["s1"].id, 0.0, treat_setup["o1"].id)
        assert res == 80.0


def test_compare_treatments_sorting(app, treat_setup):
    """Test 6: Correctly sorts treatment options by cost efficiency."""
    with app.app_context():
        # Option 1: cost = 5000, reduction = 50% (eff = 0.01)
        # Option 2: cost = 2000, reduction = 40% (eff = 0.02)
        RiskTreatmentService.create_option(
            treat_setup["s1"].id, "mitigate", "Isolation", "Desc", 5000.0, 50.0, "medium", treat_setup["o1"].id
        )
        RiskTreatmentService.create_option(
            treat_setup["s1"].id, "mitigate", "Firewall", "Desc", 2000.0, 40.0, "medium", treat_setup["o1"].id
        )
        res = RiskTreatmentService.compare_treatments(treat_setup["s1"].id, treat_setup["o1"].id)
        assert res[0]["title"] == "Firewall"


def test_recommend_treatment(app, treat_setup):
    """Test 7: Recommendations selects the most cost effective option."""
    with app.app_context():
        RiskTreatmentService.create_option(
            treat_setup["s1"].id, "mitigate", "Isolation", "Desc", 5000.0, 50.0, "medium", treat_setup["o1"].id
        )
        RiskTreatmentService.create_option(
            treat_setup["s1"].id, "mitigate", "Firewall", "Desc", 2000.0, 40.0, "medium", treat_setup["o1"].id
        )
        rec = RiskTreatmentService.recommend_treatment(treat_setup["s1"].id, treat_setup["o1"].id)
        assert rec.title == "Firewall"


def test_approve_treatment(app, treat_setup):
    """Test 8: Approving updates status and recalculates residual score."""
    with app.app_context():
        opt = RiskTreatmentService.create_option(
            treat_setup["s1"].id, "mitigate", "Isolation", "Desc", 5000.0, 50.0, "medium", treat_setup["o1"].id
        )
        approved = RiskTreatmentService.approve_treatment(opt.id, treat_setup["o1"].id)
        assert approved.status == "approved"

        # Update scenario residual
        s = QuantitativeRiskScenario.query.get(treat_setup["s1"].id)
        assert s.residual_risk_score == 40.0


def test_approve_treatment_not_found(app, treat_setup):
    """Test 9: Approve non-existent treatment returns None."""
    with app.app_context():
        assert RiskTreatmentService.approve_treatment(999, treat_setup["o1"].id) is None


def test_treatment_summary(app, treat_setup):
    """Test 10: Summary aggregates option statistics."""
    with app.app_context():
        RiskTreatmentService.create_option(
            treat_setup["s1"].id, "mitigate", "Isolation", "Desc", 5000.0, 50.0, "medium", treat_setup["o1"].id
        )
        summary = RiskTreatmentService.treatment_summary(treat_setup["o1"].id)
        assert summary["total_options"] == 1
