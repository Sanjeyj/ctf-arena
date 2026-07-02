import datetime
from app.extensions import db
from app.models.incident import Incident
from app.models.defense_action import DefenseAction
from app.services.hook_service import HookService

class IncidentService:
    @staticmethod
    def create_incident(title: str, description: str, simulation_id: int) -> Incident:
        """Create a new security incident for a simulation session."""
        incident = Incident(
            title=title,
            description=description,
            simulation_id=simulation_id,
            status='open',
            workflow_stage='detection',
            detected_at=datetime.datetime.utcnow()
        )
        db.session.add(incident)
        db.session.commit()
        return incident

    @staticmethod
    def update_stage(incident: Incident, new_stage: str) -> tuple[bool, str]:
        """Progress an incident through the IR workflow stages."""
        valid_stages = ('detection', 'analysis', 'containment', 'eradication', 'recovery', 'lessons_learned')
        if new_stage not in valid_stages:
            return False, f"Invalid stage: {new_stage}"

        incident.workflow_stage = new_stage
        
        if new_stage == 'containment' and not incident.contained_at:
            incident.contained_at = datetime.datetime.utcnow()
            incident.status = 'contained'
            # Award containment bonus to Blue Team (+10 points)
            if incident.simulation:
                incident.simulation.blue_score += 10.0

        db.session.commit()
        return True, None

    @staticmethod
    def update_status(incident: Incident, new_status: str) -> tuple[bool, str]:
        """Update incident lifecycle status."""
        valid_statuses = ('open', 'investigating', 'contained', 'resolved')
        if new_status not in valid_statuses:
            return False, f"Invalid status: {new_status}"

        incident.status = new_status
        
        if new_status == 'resolved':
            incident.resolved_at = datetime.datetime.utcnow()
            incident.workflow_stage = 'lessons_learned'
            # Trigger Hook: after_incident_close
            HookService.trigger_hook('after_incident_close', incident=incident)

        db.session.commit()
        return True, None

    @staticmethod
    def link_defense_action(incident: Incident, action: DefenseAction) -> None:
        """Associate a defense action with an incident."""
        action.incident_id = incident.id
        db.session.commit()

    @staticmethod
    def auto_triage_incident(simulation_id: int, event_details: str) -> Incident:
        """Automatically trigger an incident escalation from SOC alerts."""
        title = f"Alert: High Severity Attack Event Detected"
        description = f"Automated triage triggered incident for event details: {event_details}"
        return IncidentService.create_incident(title, description, simulation_id)
