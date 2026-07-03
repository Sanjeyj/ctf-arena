"""
PlaybookEngine Service - Phase 21 Playbook Engine.
Executes security playbooks in simulation-only mode, logging steps and transition phases.
"""
import json
from app.extensions import db
from app.models.playbook import Playbook
from app.models.playbook_execution import PlaybookExecution

class PlaybookEngineService:

    @staticmethod
    def create_playbook(name: str, description: str = "", trigger_type: str = 'manual',
                        steps: list = None, org_id: int = None) -> Playbook:
        playbook = Playbook(
            name=name,
            description=description,
            trigger_type=trigger_type,
            steps_json=json.dumps(steps or []),
            is_active=True,
            organization_id=org_id
        )
        db.session.add(playbook)
        db.session.commit()
        return playbook

    @staticmethod
    def execute_playbook(playbook_id: int, alert_id: int = None, org_id: int = None) -> PlaybookExecution:
        playbook = db.session.get(Playbook, playbook_id)
        if not playbook or not playbook.is_active:
            raise ValueError("Playbook not found or inactive")
            
        execution = PlaybookExecution(
            playbook_id=playbook_id,
            alert_id=alert_id,
            status='running',
            current_step=0,
            logs='[System] Playbook execution started.\n',
            organization_id=org_id
        )
        db.session.add(execution)
        db.session.commit()
        
        steps = json.loads(playbook.steps_json)
        for idx, step in enumerate(steps):
            execution.current_step = idx + 1
            execution.logs += f"[Step {idx+1}] Executed action: {step}\n"
            
        execution.status = 'completed'
        execution.logs += "[System] Playbook execution successfully completed.\n"
        db.session.commit()
        return execution
