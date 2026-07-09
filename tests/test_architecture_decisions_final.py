"""Tests for Architecture Decision Record FSM lifecycle transitions."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.architecture_decision_record import ArchitectureDecisionRecord
from app.services.architecture_decision_service import ArchitectureDecisionService


@pytest.fixture
def adr_setup(app):
    with app.app_context():
        db.session.query(ArchitectureDecisionRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org = Organization(name="Org A", slug="org-a")
        db.session.add(org)
        db.session.commit()
        yield {"org": org}


def test_create_decision_success(app, adr_setup):
    with app.app_context():
        rec = ArchitectureDecisionService.create_decision(
            adr_setup["org"].id, "ADR-001", "Core API Convergence", "Converge namespaces"
        )
        assert rec["id"] is not None
        assert rec["status"] == "proposed"


def test_create_decision_validation_error(app, adr_setup):
    with app.app_context():
        with pytest.raises(ValueError):
            ArchitectureDecisionService.create_decision(
                adr_setup["org"].id, "", "Title", "Decision"
            )


def test_create_decision_duplicate_rejected(app, adr_setup):
    with app.app_context():
        ArchitectureDecisionService.create_decision(
            adr_setup["org"].id, "ADR-001", "Title", "Decision"
        )
        with pytest.raises(ValueError, match="already exists"):
            ArchitectureDecisionService.create_decision(
                adr_setup["org"].id, "ADR-001", "Title 2", "Decision 2"
            )


def test_validate_transition_proposed_to_accepted(app, adr_setup):
    assert ArchitectureDecisionService.validate_transition("proposed", "accepted") is True


def test_validate_transition_proposed_to_superseded(app, adr_setup):
    assert ArchitectureDecisionService.validate_transition("proposed", "superseded") is False


def test_accept_decision_success(app, adr_setup):
    with app.app_context():
        rec = ArchitectureDecisionService.create_decision(
            adr_setup["org"].id, "ADR-001", "Title", "Decision"
        )
        accepted = ArchitectureDecisionService.accept_decision(
            adr_setup["org"].id, rec["id"], "Lead Architect"
        )
        assert accepted["status"] == "accepted"
        assert accepted["approved_by"] == "Lead Architect"


def test_accept_decision_missing_signature(app, adr_setup):
    with app.app_context():
        rec = ArchitectureDecisionService.create_decision(
            adr_setup["org"].id, "ADR-001", "Title", "Decision"
        )
        with pytest.raises(ValueError, match="signature required"):
            ArchitectureDecisionService.accept_decision(
                adr_setup["org"].id, rec["id"], ""
            )


def test_deprecate_decision(app, adr_setup):
    with app.app_context():
        rec = ArchitectureDecisionService.create_decision(
            adr_setup["org"].id, "ADR-001", "Title", "Decision"
        )
        dep = ArchitectureDecisionService.deprecate_decision(
            adr_setup["org"].id, rec["id"]
        )
        assert dep["status"] == "deprecated"


def test_supersede_decision(app, adr_setup):
    with app.app_context():
        rec = ArchitectureDecisionService.create_decision(
            adr_setup["org"].id, "ADR-001", "Title", "Decision"
        )
        # Move proposed to accepted first, as proposed cannot directly be superseded
        ArchitectureDecisionService.accept_decision(
            adr_setup["org"].id, rec["id"], "Lead Architect"
        )
        sup = ArchitectureDecisionService.supersede_decision(
            adr_setup["org"].id, rec["id"], "ADR-002"
        )
        assert sup["status"] == "superseded"
        assert "Superseded by ADR ADR-002" in sup["consequences"]


def test_decision_summary(app, adr_setup):
    with app.app_context():
        ArchitectureDecisionService.create_decision(
            adr_setup["org"].id, "ADR-001", "Title", "Decision"
        )
        sumry = ArchitectureDecisionService.decision_summary(adr_setup["org"].id)
        assert sumry["total_adrs"] == 1
        assert sumry["status_counts"]["proposed"] == 1
