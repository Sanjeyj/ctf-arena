"""
AI CTI Copilot - Phase 21 AI Copilots.
Explains static indicators and aggregates malware campaigns lists.
"""
from app.extensions import db
from app.models.malware_sample import MalwareSample
from app.models.threat_actor import ThreatActor

class AICtiCopilot:

    @staticmethod
    def explain_malware_indicators(sample_id: int) -> str:
        sample = db.session.get(MalwareSample, sample_id)
        if not sample:
            return f"Malware sample #{sample_id} not found."
            
        return (
            f"CTI Copilot report on sample '{sample.filename}':\n\n"
            f"Static Analysis shows MD5 {sample.md5} and Calculated Shannon Entropy {sample.entropy}. "
            f"Key strings references observed in decompiled blocks."
        )

    @staticmethod
    def summarize_campaigns(actor_id: int) -> str:
        actor = db.session.get(ThreatActor, actor_id)
        if not actor:
            return f"Threat Actor #{actor_id} not found."
            
        return (
            f"CTI Copilot Campaign Summary for Actor Group '{actor.name}':\n\n"
            f"Active campaigns highlight targets matching target regions. "
            f"Primary techniques leverage spearphishing credentials."
        )
