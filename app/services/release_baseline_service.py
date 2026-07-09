"""Phase 40 — Release Baseline Service.

Creates, compares, and manages release baselines.
Human approval is mandatory before any baseline transitions to 'approved'.
All operations are offline and tenant-isolated.
"""
import hashlib
import json
import logging
import datetime
from typing import Dict, List, Optional

from app.extensions import db
from app.models.release_baseline import ReleaseBaseline

logger = logging.getLogger(__name__)


class ReleaseBaselineService:
    """Manages release baselines with deterministic hashing and human approval gates."""

    @classmethod
    def collect_repository_metrics(
        cls,
        migration_revision: str,
        test_count: int,
        warning_count: int,
        model_count: int,
        service_count: int,
        route_count: int,
        template_count: int,
        documentation_count: int,
    ) -> Dict:
        """Collect and normalize repository metrics for baseline capture."""
        return {
            'migration_revision': migration_revision,
            'test_count': test_count,
            'warning_count': warning_count,
            'model_count': model_count,
            'service_count': service_count,
            'route_count': route_count,
            'template_count': template_count,
            'documentation_count': documentation_count,
        }

    @classmethod
    def calculate_baseline_hash(cls, metrics: Dict) -> str:
        """Produce a deterministic SHA-256 hash of normalized baseline metrics."""
        # Normalize: sort keys, use JSON canonical form
        normalized = json.dumps(metrics, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @classmethod
    def create_baseline(
        cls,
        org_id: int,
        version: str,
        metrics: Dict,
        codename: str = '',
        notes: str = '',
    ) -> Dict:
        """Create a new release baseline in 'draft' status."""
        if not version:
            raise ValueError("version is required")
        existing = ReleaseBaseline.query.filter_by(
            version=version, organization_id=org_id
        ).first()
        if existing:
            raise ValueError(f"Baseline version '{version}' already exists for org {org_id}")
        baseline_hash = cls.calculate_baseline_hash(metrics)
        bl = ReleaseBaseline(
            version=version,
            codename=codename,
            migration_revision=metrics.get('migration_revision', ''),
            test_count=metrics.get('test_count', 0),
            warning_count=metrics.get('warning_count', 0),
            model_count=metrics.get('model_count', 0),
            service_count=metrics.get('service_count', 0),
            route_count=metrics.get('route_count', 0),
            template_count=metrics.get('template_count', 0),
            documentation_count=metrics.get('documentation_count', 0),
            baseline_hash=baseline_hash,
            status='draft',
            notes=notes,
            organization_id=org_id,
        )
        db.session.add(bl)
        db.session.commit()
        logger.info(f"[ReleaseBaseline] Created baseline v{version} (hash={baseline_hash[:12]}...) for org {org_id}")
        return bl.to_dict()

    @classmethod
    def compare_baselines(cls, org_id: int, baseline_id_a: int, baseline_id_b: int) -> Dict:
        """Compare two baselines and return delta metrics."""
        a = ReleaseBaseline.query.filter_by(id=baseline_id_a, organization_id=org_id).first()
        b = ReleaseBaseline.query.filter_by(id=baseline_id_b, organization_id=org_id).first()
        if not a or not b:
            raise ValueError("One or both baselines not found for this org")
        return {
            'baseline_a': a.version,
            'baseline_b': b.version,
            'hash_match': a.baseline_hash == b.baseline_hash,
            'test_count_delta': b.test_count - a.test_count,
            'model_count_delta': b.model_count - a.model_count,
            'service_count_delta': b.service_count - a.service_count,
            'route_count_delta': b.route_count - a.route_count,
            'migration_changed': a.migration_revision != b.migration_revision,
        }

    @classmethod
    def approve_baseline(cls, org_id: int, baseline_id: int, approved_by: str) -> Dict:
        """Human approval gate — transition baseline from 'reviewing' to 'approved'."""
        bl = ReleaseBaseline.query.filter_by(id=baseline_id, organization_id=org_id).first()
        if not bl:
            raise ValueError(f"Baseline {baseline_id} not found for org {org_id}")
        if bl.status not in ('draft', 'reviewing'):
            raise ValueError(f"Cannot approve baseline in status '{bl.status}'")
        if not approved_by or not approved_by.strip():
            raise ValueError("Human approved_by identity is required for approval")
        bl.status = 'approved'
        bl.approved_by = approved_by.strip()
        bl.approved_at = datetime.datetime.utcnow()
        db.session.commit()
        logger.info(f"[ReleaseBaseline] Baseline {baseline_id} approved by '{approved_by}' for org {org_id}")
        return bl.to_dict()

    @classmethod
    def supersede_baseline(cls, org_id: int, baseline_id: int, superseded_by_version: str) -> Dict:
        """Mark a baseline as superseded by a newer version."""
        bl = ReleaseBaseline.query.filter_by(id=baseline_id, organization_id=org_id).first()
        if not bl:
            raise ValueError(f"Baseline {baseline_id} not found for org {org_id}")
        if bl.status == 'superseded':
            raise ValueError("Baseline is already superseded")
        bl.status = 'superseded'
        bl.notes = (bl.notes or '') + f' | Superseded by {superseded_by_version}'
        db.session.commit()
        return bl.to_dict()

    @classmethod
    def baseline_summary(cls, org_id: int) -> Dict:
        """Summarize all baselines for the tenant."""
        bls = ReleaseBaseline.query.filter_by(organization_id=org_id).order_by(
            ReleaseBaseline.created_at.desc()
        ).all()
        approved = [b for b in bls if b.status == 'approved']
        return {
            'total_baselines': len(bls),
            'approved_baselines': len(approved),
            'latest_baseline': bls[0].to_dict() if bls else None,
            'latest_approved': approved[0].to_dict() if approved else None,
        }
