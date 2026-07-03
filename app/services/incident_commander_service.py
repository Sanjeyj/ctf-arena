"""
IncidentCommander Service - Phase 21 AI Incident Commander.
Orchestrates containment phases, appends IR log steps, and prints lessons learned advisories.
"""
import json
import datetime
from app.extensions import db
from app.models.incident_commander import IncidentCommander
from app.models.incident import Incident

class IncidentCommanderService:

    @staticmethod
    def get_or_create_commander(incident_id: int, org_id: int = None) -> IncidentCommander:
        commander = IncidentCommander.query.filter_by(incident_id=incident_id).first()
        if not commander:
            inc = db.session.get(Incident, incident_id)
            if not inc:
                raise ValueError(f"Incident {incident_id} not found")
            commander = IncidentCommander(
                incident_id=incident_id,
                status='active',
                current_phase='contain',
                timeline_events_json='[]',
                ir_report='',
                lessons_learned='',
                organization_id=org_id
            )
            db.session.add(commander)
            db.session.commit()
        return commander

    @staticmethod
    def log_ir_event(incident_id: int, message: str) -> IncidentCommander:
        commander = IncidentCommanderService.get_or_create_commander(incident_id)
        
        events = json.loads(commander.timeline_events_json)
        events.append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "message": message
        })
        commander.timeline_events_json = json.dumps(events)
        db.session.commit()
        return commander

    @staticmethod
    def transition_phase(incident_id: int, new_phase: str) -> IncidentCommander:
        """Transitions phase (contain -> eradicate -> recover -> postmortem)."""
        commander = IncidentCommanderService.get_or_create_commander(incident_id)
        if new_phase not in ['contain', 'eradicate', 'recover', 'postmortem']:
            raise ValueError(f"Invalid IR phase: {new_phase}")
            
        commander.current_phase = new_phase
        IncidentCommanderService.log_ir_event(incident_id, f"Incident phase transitioned to: {new_phase}")
        
        if new_phase == 'postmortem':
            commander.status = 'completed'
            commander.ir_report = f"Incident Response Report for Incident #{incident_id}.\nStatus: Triaged & Resolved."
            commander.lessons_learned = "Deploy network host isolation playbook triggers on suspicious outbound port calls."
            
        db.session.commit()
        return commander
