"""
Resilience Service - Phase 24 Global Cyber Security Cloud.
Computes organizational cyber resilience metrics using response times, compliance rates, and incidents.
"""
from app.extensions import db
from app.models.resilience_score import ResilienceScore
from app.models.compliance_control import ComplianceControl
from app.models.incident import Incident
from app.models.risk_register import RiskRegister
from app.models.course_progress import CourseProgress

class ResilienceService:
    @staticmethod
    def calculate_resilience(organization_id: int) -> ResilienceScore:
        """Compute and record organization's resilience score metric based on actual stats."""
        # 1. Compute Compliance Controls rate (0 to 100)
        controls_query = ComplianceControl.query
        if organization_id:
            controls_query = ComplianceControl.tenant_filter(controls_query, organization_id)
        
        total_controls = controls_query.count()
        passed_controls = controls_query.filter_by(status='passed').count()
        
        if total_controls > 0:
            controls_score = (passed_controls / total_controls) * 100.0
        else:
            controls_score = 75.0  # Default baseline

        # 2. Compute Incident response time metric
        total_incidents = Incident.query.count()
        
        # Calculate response time metric (0 to 100, where 100 is fast response)
        response_time_score = 80.0
        incident_score = 90.0
        if total_incidents > 0:
            incident_score = max(0.0, 100.0 - (total_incidents * 5.0))
            # Average response time from actual resolved incident timestamps
            resolved_with_times = [
                i for i in Incident.query.all()
                if i.detected_at and i.resolved_at
            ]
            if resolved_with_times:
                avg_diff_mins = sum(
                    (i.resolved_at - i.detected_at).total_seconds() / 60.0
                    for i in resolved_with_times
                ) / len(resolved_with_times)
                response_time_score = max(10.0, min(100.0, 120.0 - avg_diff_mins))

        # 3. Training completion score — use percentage field (0-100 scale)
        all_progress = CourseProgress.query.all()
        if all_progress:
            avg_pct = sum(p.percentage for p in all_progress) / len(all_progress)
            training_score = avg_pct  # already 0-100 scale
        else:
            training_score = 85.0  # default baseline

        # 4. Risk Register mitigation score — based on low risk_score entries
        risk_query = RiskRegister.query
        if organization_id:
            risk_query = RiskRegister.tenant_filter(risk_query, organization_id)
        
        total_risks = risk_query.count()
        if total_risks > 0:
            # "mitigated" = has a mitigation_plan filled in
            mitigated_risks = risk_query.filter(
                RiskRegister.mitigation_plan.isnot(None)
            ).count()
            risk_score = (mitigated_risks / total_risks) * 100.0
        else:
            risk_score = 70.0  # default baseline

        # Calculate final aggregated resilience index
        resilience_index = (
            response_time_score * 0.2 +
            controls_score * 0.3 +
            incident_score * 0.2 +
            training_score * 0.1 +
            risk_score * 0.2
        )

        resilience_record = ResilienceScore(
            response_time=round(response_time_score, 1),
            controls=round(controls_score, 1),
            incidents=round(incident_score, 1),
            training=round(training_score, 1),
            risk=round(risk_score, 1),
            resilience=round(resilience_index, 1),
            organization_id=organization_id
        )
        
        db.session.add(resilience_record)
        db.session.commit()
        
        return resilience_record

    @staticmethod
    def get_latest_score(organization_id: int) -> ResilienceScore:
        """Fetch the most recently computed resilience score for the organization."""
        query = ResilienceScore.query
        if organization_id:
            query = ResilienceScore.tenant_filter(query, organization_id)
        
        latest = query.order_by(ResilienceScore.created_at.desc()).first()
        if not latest:
            latest = ResilienceService.calculate_resilience(organization_id)
        return latest

    @staticmethod
    def get_history(organization_id: int, limit: int = 10) -> list:
        """Fetch history of resilience scores."""
        query = ResilienceScore.query
        if organization_id:
            query = ResilienceScore.tenant_filter(query, organization_id)
        return query.order_by(ResilienceScore.created_at.desc()).limit(limit).all()
