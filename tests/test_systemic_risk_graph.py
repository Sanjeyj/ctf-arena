"""
Unit and Integration tests for Systemic Risk Graph.
Phase 39 — Systemic Cyber Risk, Collective Resilience & Federated Governance Fabric.
Contains 10 test cases.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency
from app.services.systemic_risk_graph_service import SystemicRiskGraphService
from app.research.routes import create_jwt


@pytest.fixture
def graph_setup(app):
    with app.app_context():
        db.session.query(SystemicDependency).delete()
        db.session.query(SystemicRiskNode).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Tenant A", slug="tenant-a", plan_type="enterprise")
        o2 = Organization(name="Tenant B", slug="tenant-b", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token1 = create_jwt({"username": "admin", "org_id": o1.id}, secret)
        token2 = create_jwt({"username": "admin", "org_id": o2.id}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "token1": token1,
            "token2": token2,
            "headers1": {"Authorization": f"Bearer {token1}"},
            "headers2": {"Authorization": f"Bearer {token2}"}
        }


def test_node_model_persistence(app, graph_setup):
    """Test 1: Model persistence and field boundaries."""
    with app.app_context():
        node = SystemicRiskNode(
            name="Cloud Region 1",
            node_type="cloud_region",
            criticality_score=85.0,
            organization_id=graph_setup["o1"].id
        )
        db.session.add(node)
        db.session.commit()
        assert node.id is not None
        assert node.status == "active"


def test_register_projection_service(app, graph_setup):
    """Test 2: GraphService.register_projection registers cleanly."""
    with app.app_context():
        node = SystemicRiskGraphService.register_projection(
            "Service A", "service", "platform_service", 101,
            "finance", "us-east", graph_setup["o1"].id,
            criticality_score=90.0
        )
        assert node.id is not None
        assert node.reference_id == 101


def test_register_projection_duplicates(app, graph_setup):
    """Test 3: Duplicate projections return the existing node."""
    with app.app_context():
        node1 = SystemicRiskGraphService.register_projection(
            "Service A", "service", "platform_service", 101,
            "finance", "us-east", graph_setup["o1"].id
        )
        node2 = SystemicRiskGraphService.register_projection(
            "Service A Copy", "service", "platform_service", 101,
            "finance", "us-east", graph_setup["o1"].id
        )
        assert node1.id == node2.id


def test_add_dependency_success(app, graph_setup):
    """Test 4: Add valid dependency between two tenant nodes."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", graph_setup["o1"].id)
        n2 = SystemicRiskGraphService.register_projection("N2", "service", None, None, "f", "r", graph_setup["o1"].id)
        dep = SystemicRiskGraphService.add_dependency(
            n1.id, n2.id, "technical", 70.0, 50.0, 40.0, 0.6, 80.0, graph_setup["o1"].id
        )
        assert dep.id is not None
        assert dep.propagation_probability == 0.6


def test_add_dependency_self_edge_rejected(app, graph_setup):
    """Test 5: Rejects self-edge dependency."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", graph_setup["o1"].id)
        with pytest.raises(ValueError, match="Self-edges are not permitted"):
            SystemicRiskGraphService.add_dependency(
                n1.id, n1.id, "technical", 70.0, 50.0, 40.0, 0.6, 80.0, graph_setup["o1"].id
            )


def test_add_dependency_cross_tenant_rejected(app, graph_setup):
    """Test 6: Rejects cross-tenant dependency edges."""
    with app.app_context():
        n1 = SystemicRiskRiskNode = SystemicRiskNode(
            name="Tenant A Node", node_type="service", organization_id=graph_setup["o1"].id
        )
        n2 = SystemicRiskNode(
            name="Tenant B Node", node_type="service", organization_id=graph_setup["o2"].id
        )
        db.session.add_all([n1, n2])
        db.session.commit()

        with pytest.raises(ValueError, match="Source or target node not found in this tenant"):
            SystemicRiskGraphService.add_dependency(
                n1.id, n2.id, "technical", 70.0, 50.0, 40.0, 0.6, 80.0, graph_setup["o1"].id
            )


def test_calculate_centrality(app, graph_setup):
    """Test 7: Centrality calculations are correct."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", graph_setup["o1"].id)
        n2 = SystemicRiskGraphService.register_projection("N2", "service", None, None, "f", "r", graph_setup["o1"].id)
        SystemicRiskGraphService.add_dependency(
            n1.id, n2.id, "technical", 70.0, 50.0, 40.0, 0.6, 80.0, graph_setup["o1"].id
        )
        centrality = SystemicRiskGraphService.calculate_node_centrality(graph_setup["o1"].id)
        assert centrality[n1.id] > 0.0


def test_identify_single_points_of_failure(app, graph_setup):
    """Test 8: SPOF detection works correctly."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", graph_setup["o1"].id)
        n2 = SystemicRiskGraphService.register_projection("N2", "service", None, None, "f", "r", graph_setup["o1"].id)
        n3 = SystemicRiskGraphService.register_projection("N3", "service", None, None, "f", "r", graph_setup["o1"].id)
        # N3 depends on N1 and N2 with low substitutability
        SystemicRiskGraphService.add_dependency(
            n1.id, n3.id, "technical", 70.0, 20.0, 40.0, 0.6, 80.0, graph_setup["o1"].id
        )
        SystemicRiskGraphService.add_dependency(
            n2.id, n3.id, "technical", 70.0, 20.0, 40.0, 0.6, 80.0, graph_setup["o1"].id
        )
        spofs = SystemicRiskGraphService.identify_single_points_of_failure(graph_setup["o1"].id)
        assert len(spofs) >= 1
        assert spofs[0]['node_id'] == n3.id


def test_graph_summary(app, graph_setup):
    """Test 9: Graph summary metrics match."""
    with app.app_context():
        SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", graph_setup["o1"].id)
        summary = SystemicRiskGraphService.graph_summary(graph_setup["o1"].id)
        assert summary['total_nodes'] == 1
        assert summary['total_dependencies'] == 0


def test_api_routes_get_nodes(app, client, graph_setup):
    """Test 10: API endpoints for nodes list returns 200."""
    response = client.get(
        f"/api/v1/systemic-resilience/nodes?org_id={graph_setup['o1'].id}",
        headers=graph_setup["headers1"]
    )
    assert response.status_code == 200
