from app.extensions import db
from app.models.mitre_technique import MitreTechnique
from app.models.attack_event import AttackEvent

SEED_DATA = [
    {
        'tactic': 'initial_access',
        'technique_id': 'T1566',
        'name': 'Phishing',
        'description': 'Sending emails to targets to obtain credentials or execute malicious payloads.',
        'mitigation': 'User awareness training, email filtration systems, multi-factor authentication.'
    },
    {
        'tactic': 'execution',
        'technique_id': 'T1059',
        'name': 'Command and Scripting Interpreter',
        'description': 'Executing commands or scripts (e.g. bash, PowerShell) to interact with systems.',
        'mitigation': 'Restrict script execution policies, log command-line execution, audit interpreter usage.'
    },
    {
        'tactic': 'persistence',
        'technique_id': 'T1078',
        'name': 'Valid Accounts',
        'description': 'Obtaining and using credentials of existing accounts to maintain access.',
        'mitigation': 'Enforce password complexity, implement least privilege, monitor account logins.'
    },
    {
        'tactic': 'privilege_escalation',
        'technique_id': 'T1068',
        'name': 'Exploitation for Privilege Escalation',
        'description': 'Exploiting software vulnerabilities to elevate permissions to root or SYSTEM.',
        'mitigation': 'Regular patch management, minimize running services, use vulnerability scanning.'
    },
    {
        'tactic': 'defense_evasion',
        'technique_id': 'T1070',
        'name': 'Indicator Removal on Host',
        'description': 'Deleting logs, audit trails, or artifacts to evade detection mechanisms.',
        'mitigation': 'Forward logs to centralized log server, write-once-read-many log storage.'
    },
    {
        'tactic': 'credential_access',
        'technique_id': 'T1110',
        'name': 'Brute Force',
        'description': 'Attempting multiple passwords against a service to gain valid credentials.',
        'mitigation': 'Account lockout policies, rate limiting, mandatory multi-factor authentication.'
    },
    {
        'tactic': 'discovery',
        'technique_id': 'T1087',
        'name': 'Account Discovery',
        'description': 'Listing accounts on a target host to identify potential targets.',
        'mitigation': 'Restrict access to account listings, monitor active directory queries.'
    },
    {
        'tactic': 'lateral_movement',
        'technique_id': 'T1210',
        'name': 'Exploitation of Remote Services',
        'description': 'Exploiting services running on adjacent systems to move laterally.',
        'mitigation': 'Network segmentation, firewalls between subnets, disabling unused services.'
    },
    {
        'tactic': 'collection',
        'technique_id': 'T1114',
        'name': 'Email Collection',
        'description': 'Accessing and harvesting email data from local or remote servers.',
        'mitigation': 'Encrypt mail databases, audit server mailbox access, restrict administrative tools.'
    },
    {
        'tactic': 'exfiltration',
        'technique_id': 'T1048',
        'name': 'Exfiltration Over Alternative Protocol',
        'description': 'Stealing data by transmitting it over non-standard protocols (e.g. DNS, ICMP).',
        'mitigation': 'Monitor egress network traffic, implement deep packet inspection, restrict data egress routes.'
    },
    {
        'tactic': 'impact',
        'technique_id': 'T1485',
        'name': 'Data Destruction',
        'description': 'Rendering data unusable or permanently deleting it to disrupt operations.',
        'mitigation': 'Maintain offline read-only backups, implement configuration backups, restrict admin access.'
    }
]

class MitreService:
    @staticmethod
    def seed_techniques():
        """Seed the MITRE ATT&CK techniques catalog if empty."""
        if MitreTechnique.query.first():
            return
        
        for item in SEED_DATA:
            t = MitreTechnique(
                tactic=item['tactic'],
                technique_id=item['technique_id'],
                name=item['name'],
                description=item['description'],
                mitigation=item['mitigation']
            )
            db.session.add(t)
        db.session.commit()

    @staticmethod
    def get_technique(technique_id: str) -> MitreTechnique:
        MitreService.seed_techniques()
        return MitreTechnique.query.filter_by(technique_id=technique_id).first()

    @staticmethod
    def get_tactic_techniques(tactic: str) -> list[MitreTechnique]:
        MitreService.seed_techniques()
        return MitreTechnique.query.filter_by(tactic=tactic).all()

    @staticmethod
    def map_event_to_mitre(event: AttackEvent, technique_id: str) -> bool:
        """Map an attack event to a MITRE technique and populate its technique fields."""
        tech = MitreService.get_technique(technique_id)
        if not tech:
            return False
        
        event.mitre_technique_id = tech.id
        event.technique_id = tech.technique_id
        event.technique = tech.name
        db.session.commit()
        return True

    @staticmethod
    def get_kill_chain(simulation_id: int) -> list[dict]:
        """Generate a sequential list of mapped events for visualization."""
        events = AttackEvent.query.filter_by(simulation_id=simulation_id).order_by(AttackEvent.created_at).all()
        chain = []
        for e in events:
            chain.append({
                'event_id': e.id,
                'tactic': e.tactic,
                'technique_id': e.technique_id,
                'technique_name': e.technique,
                'severity': e.severity,
                'timestamp': e.created_at.isoformat() if e.created_at else None,
                'detected': e.detected
            })
        return chain
