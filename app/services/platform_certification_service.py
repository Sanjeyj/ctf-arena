"""Phase 40 — Platform Certification Service.

Evaluates stored audit results and produces certification run scores.
No external infrastructure operations are performed.
All operations are offline, simulation-only, and tenant-isolated.
"""
import logging
import datetime
from typing import Dict, List, Optional

from app.extensions import db
from app.models.platform_certification_run import PlatformCertificationRun
from app.models.certification_check import CertificationCheck

logger = logging.getLogger(__name__)

# Category → score field mapping
CATEGORY_SCORE_MAP = {
    'security': 'security_score',
    'tenant_isolation': 'tenant_isolation_score',
    'ai_safety': 'ai_safety_score',
    'offline_safety': 'offline_safety_score',
    'migration_integrity': 'migration_integrity_score',
    'numeric_correctness': 'reliability_score',
    'route_ownership': 'security_score',
    'documentation': 'reliability_score',
    'human_approval': 'tenant_isolation_score',
    'simulation_safety': 'offline_safety_score',
}

# Status → numeric weight
CHECK_STATUS_WEIGHT = {
    'passed': 100.0,
    'warning': 70.0,
    'failed': 0.0,
    'not_applicable': None,  # excluded from scoring
}


class PlatformCertificationService:
    """Creates and scores platform certification runs from stored check results."""

    @classmethod
    def create_run(
        cls,
        org_id: int,
        name: str,
        certification_type: str = 'full_platform',
        baseline_test_count: int = 0,
    ) -> Dict:
        """Create a new certification run record."""
        if certification_type not in PlatformCertificationRun.CERT_TYPES:
            raise ValueError(f"Invalid certification_type: {certification_type}")
        run = PlatformCertificationRun(
            name=name,
            certification_type=certification_type,
            baseline_test_count=baseline_test_count,
            status='running',
            started_at=datetime.datetime.utcnow(),
            organization_id=org_id,
        )
        db.session.add(run)
        db.session.commit()
        logger.info(f"[Certification] Created run '{name}' (type={certification_type}) for org {org_id}")
        return run.to_dict()

    @classmethod
    def execute_check(
        cls,
        org_id: int,
        run_id: int,
        check_category: str,
        check_name: str,
        expected_result: str = '',
        actual_result: str = '',
        score: Optional[float] = None,
        status: str = 'passed',
        evidence_reference: str = '',
        details: str = '',
    ) -> Dict:
        """Record an individual certification check result."""
        run = PlatformCertificationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found for org {org_id}")
        if status not in CertificationCheck.STATUS_CHOICES:
            raise ValueError(f"Invalid status: {status}")

        check = CertificationCheck(
            certification_run_id=run_id,
            check_category=check_category,
            check_name=check_name,
            expected_result=expected_result,
            actual_result=actual_result,
            score=score,
            status=status,
            evidence_reference=evidence_reference,
            details=details,
            checked_at=datetime.datetime.utcnow(),
            organization_id=org_id,
        )
        db.session.add(check)
        db.session.commit()
        return check.to_dict()

    @classmethod
    def calculate_category_scores(cls, org_id: int, run_id: int) -> Dict[str, float]:
        """Compute average score per category from completed checks."""
        checks = CertificationCheck.query.filter_by(
            certification_run_id=run_id, organization_id=org_id
        ).all()
        category_scores: Dict[str, List[float]] = {}
        for chk in checks:
            weight = CHECK_STATUS_WEIGHT.get(chk.status)
            if weight is None:
                continue  # not_applicable excluded
            cat = chk.check_category
            if cat not in category_scores:
                category_scores[cat] = []
            # Use explicit score if provided, else derive from status weight
            val = float(chk.score) if chk.score is not None else weight
            category_scores[cat].append(val)

        return {
            cat: round(sum(vals) / len(vals), 4)
            for cat, vals in category_scores.items()
            if vals
        }

    @classmethod
    def calculate_overall_score(cls, category_scores: Dict[str, float]) -> float:
        """Compute overall score as simple average of category averages."""
        if not category_scores:
            return 0.0
        total = sum(category_scores.values())
        return round(total / len(category_scores), 4)

    @classmethod
    def complete_run(cls, org_id: int, run_id: int, summary: str = '') -> Dict:
        """Finalize a run: compute scores and mark completed."""
        run = PlatformCertificationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found for org {org_id}")
        cat_scores = cls.calculate_category_scores(org_id, run_id)
        overall = cls.calculate_overall_score(cat_scores)
        run.security_score = cat_scores.get('security', None)
        run.tenant_isolation_score = cat_scores.get('tenant_isolation', None)
        run.ai_safety_score = cat_scores.get('ai_safety', None)
        run.offline_safety_score = cat_scores.get('offline_safety', None)
        run.migration_integrity_score = cat_scores.get('migration_integrity', None)
        run.reliability_score = cat_scores.get('numeric_correctness', None)
        run.overall_score = overall
        run.status = 'completed' if overall >= 0 else 'failed'
        run.completed_at = datetime.datetime.utcnow()
        run.summary = summary or f"Certification completed. Overall score: {overall}"
        db.session.commit()
        return run.to_dict()

    @classmethod
    def identify_failures(cls, org_id: int, run_id: int) -> List[Dict]:
        """Return all failed checks for a given run."""
        checks = CertificationCheck.query.filter_by(
            certification_run_id=run_id,
            organization_id=org_id,
            status='failed',
        ).all()
        return [c.to_dict() for c in checks]

    @classmethod
    def certification_summary(cls, org_id: int) -> Dict:
        """Aggregate summary of all certification runs for the tenant."""
        runs = PlatformCertificationRun.query.filter_by(organization_id=org_id).all()
        completed = [r for r in runs if r.status == 'completed']
        scores = [r.overall_score for r in completed if r.overall_score is not None]
        avg = round(sum(scores) / len(scores), 4) if scores else 0.0
        return {
            'total_runs': len(runs),
            'completed_runs': len(completed),
            'failed_runs': sum(1 for r in runs if r.status == 'failed'),
            'avg_overall_score': avg,
            'latest_run': completed[-1].to_dict() if completed else None,
        }
