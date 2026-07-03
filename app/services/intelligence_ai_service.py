"""
IntelligenceAIService - Phase 27 Global Security Intelligence Network.
Provides AI-generated summaries, explanations, and recommendations.
Simulation-only: no external LLM calls.
"""
from app.models.intelligence_report import IntelligenceReport
from app.models.forecast_event import ForecastEvent


class IntelligenceAIService:
    @staticmethod
    def summarize(report_ids: list) -> str:
        """Generate an executive summary from a set of intelligence report IDs."""
        reports = IntelligenceReport.query.filter(IntelligenceReport.id.in_(report_ids)).all()
        if not reports:
            return 'No intelligence reports found for the given IDs.'
        critical = [r for r in reports if r.severity == 'critical']
        high = [r for r in reports if r.severity == 'high']
        avg_conf = round(sum(r.confidence for r in reports) / len(reports), 2)
        summary = (
            f"Intelligence Summary: {len(reports)} report(s) analyzed. "
            f"{len(critical)} critical and {len(high)} high-severity findings. "
            f"Average confidence: {avg_conf:.0%}. "
        )
        if critical:
            summary += f"Priority: {critical[0].title}."
        return summary

    @staticmethod
    def explain(report_id: int) -> str:
        """Explain an intelligence report in plain language."""
        report = IntelligenceReport.query.get(report_id)
        if not report:
            return f'Intelligence report {report_id} not found.'
        return (
            f"Report: '{report.title}' (Severity: {report.severity.upper()}). "
            f"Source: {report.source}. "
            f"Confidence: {report.confidence:.0%}. "
            f"Summary: {report.summary or 'No summary available.'}"
        )

    @staticmethod
    def recommend(org_id: int = None) -> list:
        """Return prioritized action recommendations based on active intelligence."""
        q = IntelligenceReport.query
        if org_id:
            q = IntelligenceReport.tenant_filter(q, org_id)
        reports = q.order_by(IntelligenceReport.confidence.desc()).limit(5).all()
        recommendations = []
        for r in reports:
            if r.severity == 'critical':
                action = f"IMMEDIATE ACTION: Investigate and contain '{r.title}'."
            elif r.severity == 'high':
                action = f"HIGH PRIORITY: Escalate '{r.title}' to SOC lead within 4 hours."
            else:
                action = f"MONITOR: Track '{r.title}' for further indicators."
            recommendations.append({'report_id': r.id, 'severity': r.severity, 'action': action})
        return recommendations
