"""
ResilienceEngineService - Phase 25 Cyber Resilience & Digital Enterprise.
Computes organizational cyber resilience index scorecards and forecasts failure modes.
"""
from app.extensions import db
from app.models.business_process import BusinessProcess
from app.models.business_impact_analysis import BusinessImpactAnalysis
from app.models.resilience_exercise import ResilienceExercise
from app.models.third_party_vendor import ThirdPartyVendor
from app.models.resilience_score import ResilienceScore

class ResilienceEngineService:
    @staticmethod
    def calculate_resilience_score(organization_id: int) -> dict:
        """Compute resilience score based on BIA, exercises, and vendor risk."""
        # 1. Exercise Drill Score
        exercises_query = ResilienceExercise.query
        if organization_id:
            exercises_query = ResilienceExercise.tenant_filter(exercises_query, organization_id)
        exercises = exercises_query.all()
        exercise_score = sum(e.score for e in exercises) / len(exercises) if exercises else 75.0

        # 2. Critical Business Processes RTO alignment
        bp_query = BusinessProcess.query
        if organization_id:
            bp_query = BusinessProcess.tenant_filter(bp_query, organization_id)
        bps = bp_query.all()
        # Max RTO alignment: processes with RTO < 8 hours are high value.
        # Let's say if we have processes, we score based on how many are active and have an RTO.
        process_score = 80.0
        if bps:
            aligned_count = sum(1 for bp in bps if bp.status == 'active' and bp.rto <= 24.0)
            process_score = (aligned_count / len(bps)) * 100.0

        # 3. Third Party Vendor Risk Penalty
        vendor_query = ThirdPartyVendor.query
        if organization_id:
            vendor_query = ThirdPartyVendor.tenant_filter(vendor_query, organization_id)
        vendors = vendor_query.all()
        avg_vendor_risk = sum(v.risk_score for v in vendors) / len(vendors) if vendors else 30.0
        vendor_resilience = max(0.0, 100.0 - avg_vendor_risk)

        # 4. Final Aggregated Index
        final_score = round(exercise_score * 0.4 + process_score * 0.3 + vendor_resilience * 0.3, 1)

        # Let's log/save it to the database as a ResilienceScore record (compat with Phase 24)
        try:
            score_rec = ResilienceScore(
                response_time=round(exercise_score, 1),
                controls=round(process_score, 1),
                incidents=80.0,
                training=85.0,
                risk=round(avg_vendor_risk, 1),
                resilience=final_score,
                organization_id=organization_id
            )
            db.session.add(score_rec)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return {
            'resilience_score': final_score,
            'components': {
                'exercise_score': round(exercise_score, 1),
                'process_alignment': round(process_score, 1),
                'vendor_resilience': round(vendor_resilience, 1)
            }
        }

    @staticmethod
    def forecast_failure(organization_id: int) -> dict:
        """Forecast failure possibilities and business impacts based on BIA operational/financial impacts."""
        bia_query = BusinessImpactAnalysis.query
        if organization_id:
            bia_query = BusinessImpactAnalysis.tenant_filter(bia_query, organization_id)
        bias = bia_query.all()

        total_financial_exposure = 0.0
        critical_processes = []
        failure_probability = 15.0 # baseline 15%

        for bia in bias:
            process = bia.process
            if not process:
                continue
            # Assume 1 financial_impact point = $50,000 potential downtime loss
            loss_estimate = bia.financial_impact * 50000.0
            total_financial_exposure += loss_estimate
            
            if bia.recovery_priority in ['high', 'critical'] or process.criticality in ['high', 'critical']:
                critical_processes.append({
                    'process_name': process.name,
                    'rto': process.rto,
                    'priority': bia.recovery_priority,
                    'potential_loss': loss_estimate
                })
                failure_probability += 5.0 # increase risk for each unmitigated critical process

        failure_probability = min(95.0, failure_probability)

        return {
            'failure_probability_pct': round(failure_probability, 1),
            'estimated_downtime_loss_usd': total_financial_exposure,
            'at_risk_processes': critical_processes,
            'forecast_summary': f"Forecast indicates {failure_probability:.1f}% risk of process outage with potential exposure of ${total_financial_exposure:,.2f}"
        }

    @staticmethod
    def recommend_controls(organization_id: int) -> dict:
        """Suggest resilience controls to reduce downtime risks."""
        recommendations = []
        
        # Check processes RTOs
        bp_query = BusinessProcess.query
        if organization_id:
            bp_query = BusinessProcess.tenant_filter(bp_query, organization_id)
        bps = bp_query.all()
        
        has_low_rto = any(bp.rto <= 2.0 for bp in bps)
        if has_low_rto:
            recommendations.append("Implement multi-region active-active database replication.")
            recommendations.append("Deploy hot-standby nodes for mission-critical entrypoints.")
        else:
            recommendations.append("Establish automated daily off-site backups.")

        # Check vendor risk
        vendor_query = ThirdPartyVendor.query
        if organization_id:
            vendor_query = ThirdPartyVendor.tenant_filter(vendor_query, organization_id)
        high_risk_vendors = vendor_query.filter(ThirdPartyVendor.risk_score > 60.0).count()
        if high_risk_vendors > 0:
            recommendations.append(f"Perform secondary backup system alignment for {high_risk_vendors} high-risk vendors.")
            recommendations.append("Enforce multi-factor verification requirements for vendor integrations.")

        # Check exercises
        exercise_query = ResilienceExercise.query
        if organization_id:
            exercise_query = ResilienceExercise.tenant_filter(exercise_query, organization_id)
        if exercise_query.count() == 0:
            recommendations.append("Schedule quarterly disaster recovery tabletop exercises.")

        return {
            'organization_id': organization_id,
            'recommended_actions': recommendations
        }
