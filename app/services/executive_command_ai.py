"""
ExecutiveCommandAI - Phase 29 Global Cyber Command Center.
AI-driven executive summarization, recommendations, and strategic advice for the command center.
"""
from app.extensions import db
from app.models.command_metric import CommandMetric


class ExecutiveCommandAI:
    _TOPIC_ADVICE = {
        'operations': (
            "Operations directive: Prioritize active operations by severity. "
            "Ensure all critical-severity operations have assigned commanders within 30 minutes."
        ),
        'cert': (
            "CERT guidance: Synchronize CERT readiness scores weekly. "
            "Countries with trust scores below 0.5 should undergo bilateral capability workshops."
        ),
        'wargames': (
            "Wargame strategy: Rotate blue/red team compositions each quarter to avoid strategic bias. "
            "Post-game retrospectives should feed directly into playbook updates."
        ),
        'strategy': (
            "Strategic directive: Objectives with priority=1 require executive review every 48 hours. "
            "Automate progress tracking using command metrics integration."
        ),
        'crisis': (
            "Crisis protocol: All active crisis rooms must have a designated incident commander. "
            "Severity-critical rooms require board-level notification within 15 minutes."
        ),
    }

    @classmethod
    def summarize(cls, org_id: int) -> str:
        """Generate a command-level executive summary for the organization."""
        metric = CommandMetric.query.filter_by(organization_id=org_id).first()
        if not metric:
            return (
                "Command summary: No command metrics available. "
                "Recommend initializing command centers and running first monitoring cycle."
            )
        composite = (
            metric.response_score + metric.resilience_score +
            metric.readiness_score + metric.intelligence_score
        ) / 4.0
        level = 'OPTIMAL' if composite >= 0.8 else 'ELEVATED' if composite >= 0.6 else 'CRITICAL'
        return (
            f"Command summary: Organization command readiness is {level} "
            f"(composite={composite:.2f}). "
            f"Response={metric.response_score:.2f}, "
            f"Resilience={metric.resilience_score:.2f}, "
            f"Readiness={metric.readiness_score:.2f}, "
            f"Intelligence={metric.intelligence_score:.2f}."
        )

    @classmethod
    def recommend(cls, org_id: int) -> str:
        """Provide an actionable recommendation based on the weakest command metric."""
        metric = CommandMetric.query.filter_by(organization_id=org_id).first()
        if not metric:
            return "Recommendation: Deploy command centers and run initial metric baseline."
        scores = {
            'response': metric.response_score,
            'resilience': metric.resilience_score,
            'readiness': metric.readiness_score,
            'intelligence': metric.intelligence_score,
        }
        weakest = min(scores, key=scores.get)
        improvements = {
            'response': "Improve response by running quarterly crisis room drills.",
            'resilience': "Improve resilience by stress-testing defense grids under load scenarios.",
            'readiness': "Improve readiness by synchronizing all CERT teams and command centers.",
            'intelligence': "Improve intelligence by expanding threat campaign monitoring across all regions.",
        }
        return f"Recommendation: Weakest metric is '{weakest}' ({scores[weakest]:.2f}). {improvements[weakest]}"

    @classmethod
    def advise(cls, topic: str) -> str:
        """Return strategic advice for a given command topic."""
        return cls._TOPIC_ADVICE.get(
            topic.lower(),
            f"No specific advice available for topic: '{topic}'. "
            f"Valid topics: {', '.join(cls._TOPIC_ADVICE.keys())}."
        )
