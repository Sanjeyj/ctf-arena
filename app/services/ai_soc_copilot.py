"""
AI SOC Copilot - Phase 21 AI Copilots.
Explains alert structures and recommends containment playbooks.
"""
from app.extensions import db
from app.models.alert import Alert

class AISocCopilot:

    @staticmethod
    def explain_alert(alert_id: int) -> str:
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return f"Alert #{alert_id} not found."
            
        return (
            f"SOC Copilot Analysis of Alert: '{alert.title}'\n\n"
            f"This alert indicates matching detection signatures for '{alert.severity}' severity triggers. "
            f"Review IP logs matching origin vectors."
        )

    @staticmethod
    def recommend_mitigation(alert_id: int) -> str:
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return f"Alert #{alert_id} not found."
            
        return (
            f"Recommended Mitigations:\n"
            f"1. Isolate the target client endpoint.\n"
            f"2. Apply temporary firewall block rules for source addresses.\n"
            f"3. Trigger Active Directory password reset."
        )
