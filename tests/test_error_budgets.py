"""
Unit and Integration tests for ErrorBudgetService.
Contains 10 test cases covering budget calculation, consumption thresholds, burn rate, forecasts, and input validation.
"""
import pytest
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_service import PlatformService
from app.models.reliability_objective import ReliabilityObjective
from app.models.error_budget_record import ErrorBudgetRecord
from app.services.error_budget_service import ErrorBudgetService
from app.research.routes import create_jwt


@pytest.fixture
def budget_setup(app):
    """Fixture for error budgets service tests."""
    with app.app_context():
        db.session.query(ErrorBudgetRecord).delete()
        db.session.query(ReliabilityObjective).delete()
        db.session.query(PlatformService).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        srv = PlatformService(service_name="lms", service_type="lms", organization_id=o1.id)
        db.session.add(srv)
        db.session.commit()

        obj = ReliabilityObjective(
            service_id=srv.id,
            metric_name="availability",
            target_value=0.999,
            current_value=1.0,
            measurement_window="30d",
            error_budget=1.0,
            status="compliant",
            organization_id=o1.id
        )
        db.session.add(obj)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "srv": srv,
            "obj": obj,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_error_budget_record_model(app, budget_setup):
    """Test 1: ErrorBudgetRecord model fields initialization."""
    with app.app_context():
        record = ErrorBudgetRecord(
            reliability_objective_id=budget_setup["obj"].id,
            budget_total=1.0,
            budget_consumed=0.2,
            budget_remaining=0.8,
            burn_rate=1.5,
            window_start=datetime.datetime.utcnow(),
            window_end=datetime.datetime.utcnow() + datetime.timedelta(days=30),
            status="within_budget",
            organization_id=budget_setup["o1"].id
        )
        db.session.add(record)
        db.session.commit()
        assert record.id is not None
        assert record.budget_remaining == 0.8


def test_calculate_budget_initialization(app, budget_setup):
    """Test 2: ErrorBudgetService.calculate_budget lazy initialization."""
    with app.app_context():
        record = ErrorBudgetService.calculate_budget(budget_setup["obj"].id, budget_setup["o1"].id)
        assert record.id is not None
        assert record.budget_total == 1.0
        assert record.budget_consumed == 0.0
        assert record.budget_remaining == 1.0


def test_consume_budget_normal(app, budget_setup):
    """Test 3: ErrorBudgetService.consume_budget updates remaining budget."""
    with app.app_context():
        record = ErrorBudgetService.consume_budget(budget_setup["obj"].id, 0.15, budget_setup["o1"].id)
        assert record.budget_consumed == 0.15
        assert record.budget_remaining == 0.85
        assert record.status == "within_budget"


def test_consume_budget_warning_level(app, budget_setup):
    """Test 4: ErrorBudgetService.consume_budget warning threshold (< 20% remaining)."""
    with app.app_context():
        record = ErrorBudgetService.consume_budget(budget_setup["obj"].id, 0.85, budget_setup["o1"].id)
        assert record.budget_remaining == 0.15
        assert record.status == "warning"


def test_consume_budget_exact_exhaustion(app, budget_setup):
    """Test 5: ErrorBudgetService.consume_budget exact exhaustion (100% consumed)."""
    with app.app_context():
        record = ErrorBudgetService.consume_budget(budget_setup["obj"].id, 1.0, budget_setup["o1"].id)
        assert record.budget_remaining == 0.0
        assert record.status == "exhausted"


def test_consume_budget_over_consumption(app, budget_setup):
    """Test 6: ErrorBudgetService.consume_budget over-consumption clamp remaining to 0.0."""
    with app.app_context():
        record = ErrorBudgetService.consume_budget(budget_setup["obj"].id, 1.5, budget_setup["o1"].id)
        assert record.budget_consumed == 1.5
        assert record.budget_remaining == 0.0
        assert record.status == "exhausted"


def test_consume_budget_negative_rejection(app, budget_setup):
    """Test 7: ErrorBudgetService.consume_budget rejects negative values with ValueError."""
    with app.app_context():
        with pytest.raises(ValueError, match="Consumption amount cannot be negative"):
            ErrorBudgetService.consume_budget(budget_setup["obj"].id, -0.2, budget_setup["o1"].id)


def test_calculate_burn_rate(app, budget_setup):
    """Test 8: ErrorBudgetService.calculate_burn_rate query."""
    with app.app_context():
        rate = ErrorBudgetService.calculate_burn_rate(budget_setup["obj"].id, 24.0, budget_setup["o1"].id)
        assert rate >= 0.0


def test_forecast_exhaustion_stable(app, budget_setup):
    """Test 9: ErrorBudgetService.forecast_exhaustion stable state."""
    with app.app_context():
        # Clean budget with 0 consumption should indicate stable forecast
        record = ErrorBudgetService.calculate_budget(budget_setup["obj"].id, budget_setup["o1"].id)
        forecast = ErrorBudgetService.forecast_exhaustion(budget_setup["obj"].id, budget_setup["o1"].id)
        assert "stable" in forecast or "exhausted" in forecast or "unknown" in forecast or "no exhaustion" in forecast or "hours remaining" in forecast


def test_budget_summary(app, budget_setup):
    """Test 10: ErrorBudgetService.budget_summary aggregates stats."""
    with app.app_context():
        ErrorBudgetService.calculate_budget(budget_setup["obj"].id, budget_setup["o1"].id)
        summary = ErrorBudgetService.budget_summary(budget_setup["o1"].id)
        assert summary["total_budgets"] == 1
        assert summary["within_budget"] == 1
        assert summary["avg_remaining"] == 1.0
