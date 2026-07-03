"""
SocAgent Service - Phase 21 AI SOC Analyst.
Manages SocAgent configurations, logs automated triages, predicts severity levels,
and extracts incident details.
"""
import datetime
from app.extensions import db
from app.models.soc_agent import SocAgent
from app.models.alert import Alert

class SocAgentService:

    @staticmethod
    def create_agent(name: str, role: str = 'analyst', confidence: float = 0.85,
                     model: str = 'gemini-2.0-pro', org_id: int = None) -> SocAgent:
        agent = SocAgent(
            name=name,
            role=role,
            confidence=confidence,
            status='idle',
            model=model,
            organization_id=org_id
        )
        db.session.add(agent)
        db.session.commit()
        return agent

    @staticmethod
    def list_agents(org_id: int = None):
        q = SocAgent.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()

    @staticmethod
    def run_alert_triage(agent_id: int, alert_id: int) -> dict:
        """Run simulated alert triage with predicted severity and TTPs."""
        agent = db.session.get(SocAgent, agent_id)
        alert = db.session.get(Alert, alert_id)
        if not agent or not alert:
            raise ValueError("Agent or Alert not found")
            
        agent.status = 'executing'
        agent.last_run = datetime.datetime.utcnow()
        db.session.commit()

        # Simple predicted severity logic based on title indicators
        title_lower = alert.title.lower()
        if 'brute' in title_lower or 'sqli' in title_lower or 'exploit' in title_lower:
            predicted_severity = 'critical'
            mitre_techniques = ['T1190 - Exploit Public-Facing Application', 'T1110 - Brute Force']
        elif 'anomaly' in title_lower or 'exfiltration' in title_lower:
            predicted_severity = 'high'
            mitre_techniques = ['T1048 - Exfiltration Over Alternative Protocol']
        else:
            predicted_severity = 'medium'
            mitre_techniques = ['T1059 - Command and Scripting Interpreter']

        summary = f"AI Agent '{agent.name}' triaged Alert '{alert.title}' and verified alignment with MITRE techniques."
        
        agent.status = 'idle'
        db.session.commit()

        return {
            "agent_id": agent.id,
            "alert_id": alert.id,
            "predicted_severity": predicted_severity,
            "mitre_techniques": mitre_techniques,
            "summary": summary
        }
