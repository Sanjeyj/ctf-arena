"""
Unit and Integration tests for Phase 30 — Universe Topology.
Contains 13 test cases covering domains, nodes, links topological insertion, mapping, validation, and critical paths.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.defense_universe import DefenseUniverse
from app.models.defense_domain import DefenseDomain
from app.models.universe_node import UniverseNode
from app.models.universe_link import UniverseLink
from app.services.universe_service import UniverseService
from app.services.topology_service import TopologyService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def topo_setup(app):
    """Fixture for topology tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(UniverseLink).delete()
        db.session.query(UniverseNode).delete()
        db.session.query(DefenseDomain).delete()
        db.session.query(DefenseUniverse).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Topo Org", slug="topo-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        uni = UniverseService.create_universe("Topo Uni", org.id)

        try:
            UserRepository.create(
                username="topo_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Topo Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "topo_admin"}, secret)

        yield {
            "org": org,
            "uni": uni,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_defense_domain_creation(app, topo_setup):
    """Test 1: DefenseDomain model fields."""
    with app.app_context():
        dom = DefenseDomain(
            universe_id=topo_setup["uni"].id,
            name="SOC Domain",
            domain_type="soc",
            health_score=0.9,
            readiness_score=0.8,
            organization_id=topo_setup["org"].id
        )
        db.session.add(dom)
        db.session.commit()
        assert dom.id is not None
        assert dom.name == "SOC Domain"
        assert dom.health_score == 0.9


def test_defense_domain_repr(app, topo_setup):
    """Test 2: DefenseDomain repr output."""
    with app.app_context():
        dom = DefenseDomain(name="GRC Domain", domain_type="grc", organization_id=topo_setup["org"].id)
        assert "GRC Domain" in repr(dom)
        assert "grc" in repr(dom)


def test_universe_node_creation(app, topo_setup):
    """Test 3: UniverseNode model fields."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "GRC", "grc", topo_setup["org"].id)
        node = UniverseNode(
            universe_id=topo_setup["uni"].id,
            domain_id=dom.id,
            node_name="SIEM Aggregator",
            node_type="siem",
            region="us-east-1",
            criticality="high",
            organization_id=topo_setup["org"].id
        )
        db.session.add(node)
        db.session.commit()
        assert node.id is not None
        assert node.node_name == "SIEM Aggregator"
        assert node.criticality == "high"


def test_universe_node_repr(app, topo_setup):
    """Test 4: UniverseNode repr output."""
    with app.app_context():
        node = UniverseNode(node_name="LMS Server", node_type="web", organization_id=topo_setup["org"].id)
        assert "LMS Server" in repr(node)


def test_universe_link_creation(app, topo_setup):
    """Test 5: UniverseLink model fields."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "GRC", "grc", topo_setup["org"].id)
        n1 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N1", "t1", topo_setup["org"].id)
        n2 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N2", "t2", topo_setup["org"].id)
        link = UniverseLink(
            universe_id=topo_setup["uni"].id,
            source_node_id=n1.id,
            target_node_id=n2.id,
            relationship_type="trust",
            dependency_weight=0.8,
            trust_score=0.9,
            organization_id=topo_setup["org"].id
        )
        db.session.add(link)
        db.session.commit()
        assert link.id is not None
        assert link.relationship_type == "trust"


def test_universe_link_repr(app, topo_setup):
    """Test 6: UniverseLink repr output."""
    with app.app_context():
        link = UniverseLink(source_node_id=1, target_node_id=2, relationship_type="dependency", organization_id=topo_setup["org"].id)
        assert "1->2" in repr(link)


def test_topology_service_add_domain(app, topo_setup):
    """Test 7: Service adds a domain successfully."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "Service Domain", "lms", topo_setup["org"].id)
        assert dom.id is not None
        assert dom.name == "Service Domain"


def test_topology_service_add_node(app, topo_setup):
    """Test 8: Service adds a node successfully."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "D1", "soc", topo_setup["org"].id)
        node = TopologyService.add_node(topo_setup["uni"].id, dom.id, "Test Node", "router", topo_setup["org"].id, region="EU")
        assert node.id is not None
        assert node.node_name == "Test Node"
        assert node.region == "EU"


def test_topology_service_link_nodes(app, topo_setup):
    """Test 9: Service links two nodes successfully."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "D1", "soc", topo_setup["org"].id)
        n1 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N1", "t1", topo_setup["org"].id)
        n2 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N2", "t2", topo_setup["org"].id)
        link = TopologyService.link_nodes(topo_setup["uni"].id, n1.id, n2.id, "flow", topo_setup["org"].id)
        assert link.id is not None
        assert link.source_node_id == n1.id


def test_topology_service_validate_orphans(app, topo_setup):
    """Test 10: Validate topology identifies orphaned nodes."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "D1", "soc", topo_setup["org"].id)
        n1 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N1", "t1", topo_setup["org"].id)
        n2 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N2", "t2", topo_setup["org"].id)
        
        res = TopologyService.validate_topology(topo_setup["uni"].id, topo_setup["org"].id)
        assert res["status"] == "warning"
        assert n1.id in res["orphaned_nodes"]

        # Link them
        TopologyService.link_nodes(topo_setup["uni"].id, n1.id, n2.id, "flow", topo_setup["org"].id)
        res2 = TopologyService.validate_topology(topo_setup["uni"].id, topo_setup["org"].id)
        assert res2["status"] == "valid"
        assert len(res2["orphaned_nodes"]) == 0


def test_topology_service_dependency_map(app, topo_setup):
    """Test 11: Service generates dependency adjacency lists."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "D1", "soc", topo_setup["org"].id)
        n1 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N1", "t1", topo_setup["org"].id)
        n2 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "N2", "t2", topo_setup["org"].id)
        TopologyService.link_nodes(topo_setup["uni"].id, n1.id, n2.id, "flow", topo_setup["org"].id, dependency_weight=0.7)

        dmap = TopologyService.dependency_map(topo_setup["uni"].id, topo_setup["org"].id)
        assert n1.id in dmap["nodes"]
        assert len(dmap["adjacency_list"][n1.id]) == 1
        assert dmap["adjacency_list"][n1.id][0]["weight"] == 0.7


def test_topology_service_critical_paths(app, topo_setup):
    """Test 12: Service lists critical paths sorted descending by weight."""
    with app.app_context():
        dom = TopologyService.add_domain(topo_setup["uni"].id, "D1", "soc", topo_setup["org"].id)
        n1 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "Node Low", "t1", topo_setup["org"].id, criticality="low")
        n2 = TopologyService.add_node(topo_setup["uni"].id, dom.id, "Node Critical", "t2", topo_setup["org"].id, criticality="critical")
        
        paths = TopologyService.calculate_critical_paths(topo_setup["uni"].id, topo_setup["org"].id)
        assert paths[0]["node_name"] == "Node Critical"
        assert paths[1]["node_name"] == "Node Low"


def test_api_get_topology(client, topo_setup):
    """Test 13: GET /api/v1/universe/<id>/topology REST endpoint."""
    with client.application.app_context():
        TopologyService.add_domain(topo_setup["uni"].id, "API GRC", "grc", topo_setup["org"].id)

    resp = client.get(
        f'/api/v1/universe/{topo_setup["uni"].id}/topology?org_id={topo_setup["org"].id}',
        headers=topo_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data["domains"]) >= 1
    assert data["domains"][0]["name"] == "API GRC"
