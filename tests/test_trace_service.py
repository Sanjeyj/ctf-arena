"""
Unit and Integration tests for TraceService.
Contains 10 test cases covering trace initiation, child spans, tree building, cycle protection, and critical path calculations.
"""
import pytest
import datetime
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.trace_record import TraceRecord
from app.services.trace_service import TraceService
from app.research.routes import create_jwt


@pytest.fixture
def trace_setup(app):
    """Fixture for trace service tests."""
    with app.app_context():
        db.session.query(TraceRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_trace_record_model(app, trace_setup):
    """Test 1: TraceRecord model fields and initialization."""
    with app.app_context():
        tr = TraceRecord(
            trace_id="t-100",
            span_id="s-1",
            service_name="auth",
            operation_name="login",
            organization_id=trace_setup["o1"].id,
            started_at=datetime.datetime.utcnow(),
            completed_at=datetime.datetime.utcnow()
        )
        db.session.add(tr)
        db.session.commit()
        assert tr.id is not None
        assert tr.trace_id == "t-100"


def test_start_trace(app, trace_setup):
    """Test 2: TraceService.start_trace root creation."""
    with app.app_context():
        t = TraceService.start_trace("t-200", "s-root", "auth", "login", trace_setup["o1"].id)
        assert t.id is not None
        assert t.parent_span_id is None
        assert t.service_name == "auth"


def test_add_span(app, trace_setup):
    """Test 3: TraceService.add_span child creation."""
    with app.app_context():
        TraceService.start_trace("t-200", "s-root", "auth", "login", trace_setup["o1"].id)
        c = TraceService.add_span("t-200", "s-child", "s-root", "db", "query_user", trace_setup["o1"].id)
        assert c.id is not None
        assert c.parent_span_id == "s-root"


def test_complete_span(app, trace_setup):
    """Test 4: TraceService.complete_span state transition."""
    with app.app_context():
        TraceService.start_trace("t-200", "s-root", "auth", "login", trace_setup["o1"].id)
        t = TraceService.complete_span("s-root", 120.5, "success", trace_setup["o1"].id, {"ip": "127.0.0.1"})
        assert t.duration_ms == 120.5
        assert t.status == "success"


def test_build_trace_tree(app, trace_setup):
    """Test 5: TraceService.build_trace_tree tree output."""
    with app.app_context():
        TraceService.start_trace("t-300", "s-root", "auth", "login", trace_setup["o1"].id)
        TraceService.add_span("t-300", "s-c1", "s-root", "db", "find_user", trace_setup["o1"].id)
        TraceService.complete_span("s-root", 100.0, "success", trace_setup["o1"].id)
        TraceService.complete_span("s-c1", 50.0, "success", trace_setup["o1"].id)

        tree = TraceService.build_trace_tree("t-300", trace_setup["o1"].id)
        assert tree["trace_id"] == "t-300"
        assert len(tree["roots"]) == 1
        assert len(tree["roots"][0]["children"]) == 1


def test_build_trace_tree_cycle_protection(app, trace_setup):
    """Test 6: TraceService.build_trace_tree handles cycles without crash."""
    with app.app_context():
        # Create mutual cycles: child refers to parent, parent refers to child
        t1 = TraceService.start_trace("t-cycle", "s-1", "service-a", "op-1", trace_setup["o1"].id)
        t2 = TraceService.add_span("t-cycle", "s-2", "s-1", "service-b", "op-2", trace_setup["o1"].id)

        # Force a cycle by editing database records directly
        t1.parent_span_id = "s-2"
        db.session.commit()

        tree = TraceService.build_trace_tree("t-cycle", trace_setup["o1"].id)
        # Verify it handled it and did not trigger recursion overflow error
        assert len(tree["roots"]) == 2  # Roots includes both since they form a cycle link


def test_calculate_critical_path(app, trace_setup):
    """Test 7: TraceService.calculate_critical_path correctly identifies longest sequence."""
    with app.app_context():
        TraceService.start_trace("t-crit", "s-root", "gateway", "incoming", trace_setup["o1"].id)
        TraceService.add_span("t-crit", "s-left", "s-root", "auth", "check", trace_setup["o1"].id)
        TraceService.add_span("t-crit", "s-right", "s-root", "db", "fetch", trace_setup["o1"].id)

        TraceService.complete_span("s-root", 10.0, "success", trace_setup["o1"].id)
        TraceService.complete_span("s-left", 50.0, "success", trace_setup["o1"].id)
        TraceService.complete_span("s-right", 150.0, "success", trace_setup["o1"].id)

        path = TraceService.calculate_critical_path("t-crit", trace_setup["o1"].id)
        path_ids = [s["span_id"] for s in path]
        assert "s-root" in path_ids
        assert "s-right" in path_ids
        assert "s-left" not in path_ids  # Because s-right duration is longer (150 > 50)


def test_critical_path_cycle_protection(app, trace_setup):
    """Test 8: TraceService.calculate_critical_path handles cycles safely."""
    with app.app_context():
        t1 = TraceService.start_trace("t-cycle2", "s-1", "s-a", "op-a", trace_setup["o1"].id)
        t2 = TraceService.add_span("t-cycle2", "s-2", "s-1", "s-b", "op-b", trace_setup["o1"].id)
        t1.parent_span_id = "s-2"
        db.session.commit()

        path = TraceService.calculate_critical_path("t-cycle2", trace_setup["o1"].id)
        assert len(path) <= 2


def test_trace_summary(app, trace_setup):
    """Test 9: TraceService.trace_summary calculations."""
    with app.app_context():
        TraceService.start_trace("t-sum", "s-1", "s-a", "op-a", trace_setup["o1"].id)
        TraceService.complete_span("s-1", 10.0, "error", trace_setup["o1"].id)

        summary = TraceService.trace_summary(trace_setup["o1"].id)
        assert summary["total_spans"] == 1
        assert summary["total_traces"] == 1
        assert summary["error_rate"] == 1.0


def test_trace_tenant_isolation(app, trace_setup):
    """Test 10: Spans and critical paths are tenant isolated."""
    with app.app_context():
        TraceService.start_trace("t-tenant", "s-1", "s-a", "op-a", trace_setup["o1"].id)

        # Attempt to build tree or fetch trace details using Tenant 2 org_id
        tree = TraceService.build_trace_tree("t-tenant", trace_setup["o2"].id)
        assert len(tree.get("roots", [])) == 0
