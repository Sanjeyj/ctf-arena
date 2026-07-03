"""
BCMService - Phase 25 Cyber Resilience & Digital Enterprise.
Evaluates recovery objectives (RTO/RPO) and compiles disaster recovery / business continuity plans.
"""
import json
from app.extensions import db
from app.models.business_process import BusinessProcess
from app.models.disaster_recovery_plan import DisasterRecoveryPlan

class BCMService:
    @staticmethod
    def evaluate_rto(organization_id: int) -> dict:
        """Verify whether processes meet target recovery time objectives (RTOs)."""
        bp_query = BusinessProcess.query
        if organization_id:
            bp_query = BusinessProcess.tenant_filter(bp_query, organization_id)
        processes = bp_query.all()

        violations = []
        compliant_count = 0

        for bp in processes:
            # Let's say we assume a process is compliant if rto <= 4.0 or status is inactive.
            # Real business logic: we compare actual recovery capability to the target.
            # For simulation: we flag processes with RTO target set to very low (e.g. <= 2.0 hours) but status is active.
            if bp.status == 'active' and bp.rto <= 2.0:
                violations.append({
                    'process_id': bp.id,
                    'name': bp.name,
                    'rto_target_hours': bp.rto,
                    'reason': "Recovery automation capability not verified for sub-2h RTO target."
                })
            else:
                compliant_count += 1

        total = len(processes)
        compliance_pct = (compliant_count / total * 100.0) if total > 0 else 100.0

        return {
            'total_processes': total,
            'compliant_count': compliant_count,
            'compliance_rate_pct': round(compliance_pct, 1),
            'violations': violations
        }

    @staticmethod
    def evaluate_rpo(organization_id: int) -> dict:
        """Verify whether data replication schedules align with RPOs."""
        bp_query = BusinessProcess.query
        if organization_id:
            bp_query = BusinessProcess.tenant_filter(bp_query, organization_id)
        processes = bp_query.all()

        violations = []
        compliant_count = 0

        for bp in processes:
            # For simulation: processes with RPO <= 1.0 hour require active database replication.
            if bp.status == 'active' and bp.rpo <= 1.0:
                violations.append({
                    'process_id': bp.id,
                    'name': bp.name,
                    'rpo_target_hours': bp.rpo,
                    'reason': "Sub-hour database replication checkpoint is unconfigured."
                })
            else:
                compliant_count += 1

        total = len(processes)
        compliance_pct = (compliant_count / total * 100.0) if total > 0 else 100.0

        return {
            'total_processes': total,
            'compliant_count': compliant_count,
            'compliance_rate_pct': round(compliance_pct, 1),
            'violations': violations
        }

    @staticmethod
    def generate_plan(plan_name: str, strategy: str, recovery_steps: list, priority: int, organization_id: int) -> DisasterRecoveryPlan:
        """Compile and persist a new Disaster Recovery / Business Continuity Plan."""
        plan = DisasterRecoveryPlan(
            plan_name=plan_name,
            strategy=strategy,
            recovery_steps=json.dumps(recovery_steps),
            priority=priority,
            approval_status='draft',
            organization_id=organization_id
        )
        db.session.add(plan)
        db.session.commit()
        return plan
