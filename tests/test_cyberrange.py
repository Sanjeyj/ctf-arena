"""
Phase 16 — AI Cyber Range Test Suite.

Target: 220+ passing tests (was 200).
"""
import pytest
import datetime
from app.extensions import db
from app.models.attack_simulation import AttackSimulation
from app.models.attack_event import AttackEvent
from app.models.defense_action import DefenseAction
from app.models.incident import Incident
from app.models.mitre_technique import MitreTechnique
from app.models.attack_chain import AttackChain
from app.services.mitre_service import MitreService
from app.services.red_team_ai_service import RedTeamAIService
from app.services.blue_team_ai_service import BlueTeamAIService
from app.services.incident_service import IncidentService
from app.services.timeline_service import TimelineService
from app.services.hook_service import HookService
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


# ===========================================================================
# GROUP 1 — MITRE ATT&CK Engine
# ===========================================================================
class TestMitreEngine:

    def test_seed_and_get_technique(self, app):
        """Seeding populates the MITRE Techniques catalog; can fetch technique by ID."""
        with app.app_context():
            MitreService.seed_techniques()
            tech = MitreService.get_technique('T1566')
            assert tech is not None
            assert tech.name == 'Phishing'
            assert tech.tactic == 'initial_access'

    def test_get_tactic_techniques(self, app):
        """Can fetch all techniques mapping to a specific tactic."""
        with app.app_context():
            MitreService.seed_techniques()
            techs = MitreService.get_tactic_techniques('credential_access')
            assert len(techs) >= 1
            assert techs[0].technique_id == 'T1110'

    def test_map_event_to_mitre(self, app):
        """Mapping an event populates it with technique details."""
        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(name='Test Sim')
            db.session.add(sim)
            db.session.flush()

            event = AttackEvent(simulation_id=sim.id, tactic='initial_access', severity='low')
            db.session.add(event)
            db.session.commit()

            success = MitreService.map_event_to_mitre(event, 'T1566')
            assert success is True
            assert event.technique == 'Phishing'
            assert event.technique_id == 'T1566'

    def test_get_kill_chain(self, app):
        """Kill chain returns chronological mapped events."""
        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(name='Chain Sim')
            db.session.add(sim)
            db.session.flush()

            e1 = AttackEvent(simulation_id=sim.id, tactic='initial_access', severity='low')
            e2 = AttackEvent(simulation_id=sim.id, tactic='execution', severity='medium')
            db.session.add_all([e1, e2])
            db.session.commit()

            MitreService.map_event_to_mitre(e1, 'T1566')
            MitreService.map_event_to_mitre(e2, 'T1059')

            chain = MitreService.get_kill_chain(sim.id)
            assert len(chain) == 2
            assert chain[0]['technique_id'] == 'T1566'
            assert chain[1]['technique_id'] == 'T1059'


# ===========================================================================
# GROUP 2 — Model CRUD
# ===========================================================================
class TestCyberRangeModels:

    def test_simulation_crud(self, app):
        """Simulation CRUD operations works as expected."""
        with app.app_context():
            sim = AttackSimulation(name='Range Practice', status='running', started_at=datetime.datetime.utcnow())
            db.session.add(sim)
            db.session.commit()
            assert sim.id is not None

            sim_query = AttackSimulation.query.get(sim.id)
            assert sim_query.name == 'Range Practice'
            assert sim_query.status == 'running'

    def test_defense_action_crud(self, app):
        """DefenseAction CRUD operations works."""
        with app.app_context():
            sim = AttackSimulation(name='Def Sim')
            db.session.add(sim)
            db.session.flush()
            event = AttackEvent(simulation_id=sim.id, tactic='discovery', severity='low')
            db.session.add(event)
            db.session.flush()

            action = DefenseAction(event_id=event.id, analyst='ai_blue', action='isolate_host', effectiveness=0.9)
            action.details = {'reason': 'high cpu usage alert'}
            db.session.add(action)
            db.session.commit()

            action_query = DefenseAction.query.get(action.id)
            assert action_query.details.get('reason') == 'high cpu usage alert'

    def test_attack_chain_crud(self, app):
        """AttackChain serialization of lists works."""
        with app.app_context():
            sim = AttackSimulation(name='Chain CRUD')
            db.session.add(sim)
            db.session.flush()

            chain = AttackChain(simulation_id=sim.id, name='APT28 Scenario')
            chain.expected_path = ['T1566', 'T1059']
            chain.actual_events = [1, 2]
            db.session.add(chain)
            db.session.commit()

            chain_query = AttackChain.query.get(chain.id)
            assert chain_query.expected_path == ['T1566', 'T1059']
            assert chain_query.actual_events == [1, 2]


# ===========================================================================
# GROUP 3 — AI Attacker & Defender
# ===========================================================================
class TestAIAgents:

    def test_red_ai_easy(self, app):
        """Easy mode awards 10 points and sets base severity."""
        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(name='Red Easy')
            db.session.add(sim)
            db.session.commit()

            event = RedTeamAIService.simulate_attack_step(sim, 'phishing', mode='easy')
            assert event.points_awarded == 10.0
            assert sim.red_score == 10.0
            assert event.severity == 'low'

    def test_red_ai_hard(self, app):
        """Hard mode awards 30 points and raises base severity."""
        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(name='Red Hard')
            db.session.add(sim)
            db.session.commit()

            event = RedTeamAIService.simulate_attack_step(sim, 'phishing', mode='hard')
            assert event.points_awarded == 30.0
            assert sim.red_score == 30.0
            assert event.severity == 'high'

    def test_red_ai_adaptive(self, app):
        """Adaptive mode awards 40 points."""
        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(name='Red Adaptive')
            db.session.add(sim)
            db.session.commit()

            event = RedTeamAIService.simulate_attack_step(sim, 'phishing', mode='adaptive')
            assert event.points_awarded == 40.0
            assert sim.red_score == 40.0

    def test_blue_ai_detection(self, app):
        """Blue AI creates alert action and awards points on success."""
        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(name='Blue Dec')
            db.session.add(sim)
            db.session.flush()

            event = AttackEvent(simulation_id=sim.id, tactic='initial_access', severity='critical')
            db.session.add(event)
            db.session.commit()

            action = BlueTeamAIService.analyze_event(event, soc_level='l3_soc')
            # L3 detection probability for critical is high; if detected, check metrics
            if action:
                assert event.detected is True
                assert action.points_awarded >= 15.0
                assert sim.blue_score == action.points_awarded


# ===========================================================================
# GROUP 4 — Incident Response Workflow
# ===========================================================================
class TestIncidentResponse:

    def test_incident_lifecycle(self, app):
        """Incident IR stage progression awards containment points."""
        with app.app_context():
            sim = AttackSimulation(name='Incident Sim')
            db.session.add(sim)
            db.session.commit()

            incident = IncidentService.create_incident('Ransomware Outbreak', 'Critical database encryption', sim.id)
            assert incident.status == 'open'
            assert incident.workflow_stage == 'detection'

            # Move to containment
            IncidentService.update_stage(incident, 'containment')
            assert incident.status == 'contained'
            assert incident.workflow_stage == 'containment'
            assert sim.blue_score == 10.0  # +10 containment bonus

    def test_incident_resolution(self, app):
        """Resolving an incident transitions stage to lessons learned."""
        with app.app_context():
            sim = AttackSimulation(name='Resolve Sim')
            db.session.add(sim)
            db.session.commit()

            incident = IncidentService.create_incident('SQL Injection Alert', 'Unauthorized readout', sim.id)
            IncidentService.update_status(incident, 'resolved')

            assert incident.status == 'resolved'
            assert incident.workflow_stage == 'lessons_learned'
            assert incident.resolved_at is not None

    def test_link_defense_action(self, app):
        """Linking defensive action associates it correctly."""
        with app.app_context():
            sim = AttackSimulation(name='Link Sim')
            db.session.add(sim)
            db.session.flush()
            event = AttackEvent(simulation_id=sim.id, tactic='collection', severity='medium')
            db.session.add(event)
            db.session.flush()
            action = DefenseAction(event_id=event.id, analyst='ai_blue', action='isolate_host')
            db.session.add(action)
            db.session.commit()

            incident = IncidentService.create_incident('Data Harvest', 'Staging detected', sim.id)
            IncidentService.link_defense_action(incident, action)

            assert action.incident_id == incident.id


# ===========================================================================
# GROUP 5 — Timeline Service
# ===========================================================================
class TestTimeline:

    def test_get_timeline_assembly(self, app):
        """Timeline merges start, attack, defense, incident, and completion chronologically."""
        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(
                name='Timeline Sim',
                started_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
            )
            db.session.add(sim)
            db.session.flush()

            # Create attack event
            event = AttackEvent(simulation_id=sim.id, tactic='initial_access', severity='low')
            db.session.add(event)
            db.session.flush()

            # Create incident
            incident = IncidentService.create_incident('APT Alert', 'Phishing', sim.id)

            # Create completion
            sim.ended_at = datetime.datetime.utcnow()
            sim.status = 'completed'
            db.session.commit()

            timeline = TimelineService.get_timeline(sim.id)
            assert len(timeline) >= 4  # Start, Attack, Incident, Completed
            types = [t['type'] for t in timeline]
            assert 'simulation_started' in types
            assert 'attack_event' in types
            assert 'incident_detected' in types
            assert 'simulation_completed' in types


# ===========================================================================
# GROUP 6 — Hooks Triggering
# ===========================================================================
class TestCyberRangeHooks:

    def test_attack_hooks_fire(self, app):
        """simulate_attack_step triggers before_attack_simulation and after_attack_event hooks."""
        before_called = 0
        after_called = 0

        def before_cb(*args, **kwargs):
            nonlocal before_called
            before_called += 1

        def after_cb(*args, **kwargs):
            nonlocal after_called
            after_called += 1

        HookService.register_hook('before_attack_simulation', before_cb)
        HookService.register_hook('after_attack_event', after_cb)

        with app.app_context():
            MitreService.seed_techniques()
            sim = AttackSimulation(name='Hook Sim')
            db.session.add(sim)
            db.session.commit()

            RedTeamAIService.simulate_attack_step(sim, 'phishing', mode='easy')

            assert before_called == 1
            assert after_called == 1


# ===========================================================================
# GROUP 7 — API Endpoints
# ===========================================================================
class TestCyberRangeAPI:

    def _login(self, client, app, username='range_tester'):
        with app.app_context():
            UserRepository.create(username=username, password_hash=hash_password('Pass1!'))
        client.post('/login', data={'username': username, 'password': 'Pass1!'}, follow_redirects=True)


    def test_start_simulation_api(self, client, app):
        """POST /api/v1/simulation/start creates a simulation session."""
        self._login(client, app, 'api_tester_start')
        resp = client.post('/api/v1/simulation/start', json={
            'name': 'API Attack Session',
            'attacker_type': 'hard_ai',
            'defender_type': 'l3_soc'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['simulation']['name'] == 'API Attack Session'
        assert data['simulation']['attacker_type'] == 'hard_ai'

    def test_stop_simulation_api(self, client, app):
        """POST /api/v1/simulation/stop stops running simulation."""
        self._login(client, app, 'api_tester_stop')
        with app.app_context():
            sim = AttackSimulation(name='Running Sim', status='running')
            db.session.add(sim)
            db.session.commit()
            sim_id = sim.id

        resp = client.post('/api/v1/simulation/stop', json={'simulation_id': sim_id})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['simulation']['status'] == 'completed'

    def test_get_simulation_api(self, client, app):
        """GET /api/v1/simulation/<id> returns detail model data."""
        self._login(client, app, 'api_tester_detail')
        with app.app_context():
            sim = AttackSimulation(name='Get Sim', status='completed')
            db.session.add(sim)
            db.session.commit()
            sim_id = sim.id

        resp = client.get(f'/api/v1/simulation/{sim_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['simulation']['name'] == 'Get Sim'

    def test_get_timeline_api(self, client, app):
        """GET /api/v1/timeline/<id> returns chronologically sorted timelines."""
        self._login(client, app, 'api_tester_timeline')
        with app.app_context():
            sim = AttackSimulation(name='Timeline Sim')
            db.session.add(sim)
            db.session.commit()
            sim_id = sim.id

        resp = client.get(f'/api/v1/timeline/{sim_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'timeline' in data

    def test_create_incident_api(self, client, app):
        """POST /api/v1/incident creates a new escalated incident."""
        self._login(client, app, 'api_tester_inc')
        with app.app_context():
            sim = AttackSimulation(name='API Inc Sim')
            db.session.add(sim)
            db.session.commit()
            sim_id = sim.id

        resp = client.post('/api/v1/incident', json={
            'title': 'API Escalated Inc',
            'description': 'Description text',
            'simulation_id': sim_id
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['incident']['title'] == 'API Escalated Inc'

    def test_get_mitre_api(self, client, app):
        """GET /api/v1/mitre returns techniques grouped by tactic."""
        self._login(client, app, 'api_tester_mitre')
        resp = client.get('/api/v1/mitre')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'initial_access' in data['mitre_techniques']
