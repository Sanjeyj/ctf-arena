"""
Unit and Integration tests for Step 4 Security Knowledge Graph.
"""
import pytest
import json
from app.extensions import db
from app.models.knowledge_node import KnowledgeNode
from app.models.knowledge_edge import KnowledgeEdge
from app.models.organization import Organization
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.research.routes import create_jwt

@pytest.fixture
def graph_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(KnowledgeEdge).delete()
        db.session.query(KnowledgeNode).delete()
        db.session.commit()

        org = Organization(name="Graph Org", slug="graph-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "graph_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_knowledge_graph_entities_linking(app, graph_setup):
    """Test registering nodes and setting up directional link edges."""
    with app.app_context():
        org = graph_setup['org']

        node1 = KnowledgeGraphService.add_node("actor", "APT28", {"origin": "Russia"}, org_id=org.id)
        node2 = KnowledgeGraphService.add_node("campaign", "Operation Windigo", {"year": 2026}, org_id=org.id)
        
        edge = KnowledgeGraphService.add_edge(node1.id, node2.id, "mapped_to", org_id=org.id)
        assert edge.id is not None
        assert edge.relationship == "mapped_to"

        # Traversal links mapping
        assert node1.edges_out[0].id == edge.id
        assert node2.edges_in[0].id == edge.id

def test_knowledge_graph_compilation(app, graph_setup):
    """Test compiling full graph nodes and links adjacency lists."""
    with app.app_context():
        org = graph_setup['org']

        node1 = KnowledgeGraphService.add_node("actor", "APT29", org_id=org.id)
        node2 = KnowledgeGraphService.add_node("malware", "CozyDuke", org_id=org.id)
        KnowledgeGraphService.add_edge(node1.id, node2.id, "uses", org_id=org.id)

        graph = KnowledgeGraphService.get_full_graph(org_id=org.id)
        assert len(graph['nodes']) == 2
        assert len(graph['links']) == 1

def test_knowledge_api_endpoint(client, graph_setup):
    """Test GET /api/v1/knowledge endpoint."""
    headers = graph_setup['headers']
    org = graph_setup['org']

    with client.application.app_context():
        KnowledgeGraphService.add_node("ioc", "192.168.1.100", org_id=org.id)

    resp = client.get('/api/v1/knowledge', headers=headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)['graph']
    assert len(data['nodes']) == 1
    assert data['nodes'][0]['node_type'] == "ioc"


def test_knowledge_graph_empty_retrieval(app):
    """Test retrieving graph nodes on clean org returns empty lists."""
    with app.app_context():
        res = KnowledgeGraphService.get_full_graph(org_id=9999)
        assert len(res['nodes']) == 0
        assert len(res['links']) == 0


def test_knowledge_node_serialization(app, graph_setup):
    """Test serializing nodes dictionary includes properties."""
    with app.app_context():
        org = graph_setup['org']
        node = KnowledgeGraphService.add_node("actor", "APT_Test", {"country": "US"}, org_id=org.id)
        assert node.to_dict()['properties']['country'] == "US"


def test_knowledge_edge_unauthorized_api(client, graph_setup):
    """Test GET /api/v1/knowledge returns 401 when token is missing."""
    resp = client.get('/api/v1/knowledge')
    assert resp.status_code == 401


def test_incident_commander_triage_events(app, graph_setup):
    """Test logging events in Incident Commander updates timeline JSON."""
    with app.app_context():
        from app.models.incident import Incident
        from app.models.attack_simulation import AttackSimulation
        org = graph_setup['org']
        
        sim = AttackSimulation(name="Sim 1", organization_id=org.id)
        db.session.add(sim)
        db.session.commit()
        
        inc = Incident(title="Breach incident", simulation_id=sim.id)
        db.session.add(inc)
        db.session.commit()
        
        from app.services.incident_commander_service import IncidentCommanderService
        com = IncidentCommanderService.get_or_create_commander(inc.id, org_id=org.id)
        assert com.incident_id == inc.id
        
        updated = IncidentCommanderService.log_ir_event(inc.id, "Host isolated")
        events = json.loads(updated.timeline_events_json)
        assert len(events) == 1
        assert events[0]['message'] == "Host isolated"


def test_incident_commander_phase_transition(app, graph_setup):
    """Test Incident Commander phase transition updates status and timeline."""
    with app.app_context():
        from app.models.incident import Incident
        from app.models.attack_simulation import AttackSimulation
        from app.services.incident_commander_service import IncidentCommanderService
        org = graph_setup['org']
        
        sim = AttackSimulation(name="Sim 2", organization_id=org.id)
        db.session.add(sim)
        db.session.commit()
        
        inc = Incident(title="Ransomware incident", simulation_id=sim.id)
        db.session.add(inc)
        db.session.commit()
        
        IncidentCommanderService.transition_phase(inc.id, "eradicate")
        com = IncidentCommanderService.get_or_create_commander(inc.id)
        assert com.current_phase == "eradicate"


def test_incident_commander_lessons_learned(app, graph_setup):
    """Test transitioning to postmortem outputs final IR report and lessons learned."""
    with app.app_context():
        from app.models.incident import Incident
        from app.models.attack_simulation import AttackSimulation
        from app.services.incident_commander_service import IncidentCommanderService
        org = graph_setup['org']
        
        sim = AttackSimulation(name="Sim 3", organization_id=org.id)
        db.session.add(sim)
        db.session.commit()
        
        inc = Incident(title="Exfiltration incident", simulation_id=sim.id)
        db.session.add(inc)
        db.session.commit()
        
        IncidentCommanderService.transition_phase(inc.id, "postmortem")
        com = IncidentCommanderService.get_or_create_commander(inc.id)
        assert com.status == "completed"
        assert "host isolation" in com.lessons_learned



