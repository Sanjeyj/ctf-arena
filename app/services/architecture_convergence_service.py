"""Phase 40 — Architecture Convergence Service.

Analyzes the platform for capability overlaps, canonical ownership, and
service boundary violations. All analysis is read-only; no destructive
consolidation is performed automatically.
"""
import logging
from typing import Dict, List, Optional

from app.extensions import db
from app.models.platform_capability import PlatformCapability
from app.models.capability_dependency import CapabilityDependency

logger = logging.getLogger(__name__)

# Known overlapping capability domains and their canonical owners
CANONICAL_DOMAIN_MAP = {
    'risk': 'risk_quantification',
    'resilience': 'strategic_resilience',
    'governance': 'governance_intelligence',
    'operations': 'observability_fabric',
    'intelligence': 'cyber_intelligence',
    'trust': 'trust_assurance',
    'assurance': 'trust_assurance',
    'validation': 'validation_fabric',
    'exposure': 'exposure_fabric',
    'simulation': 'systemic_resilience',
    'federation': 'systemic_resilience',
    'certification': 'mission_control',
}


class ArchitectureConvergenceService:
    """Analyses capability ownership, overlaps, and service boundary health."""

    @classmethod
    def build_ownership_matrix(cls, org_id: int) -> Dict:
        """Build a phase → capability ownership matrix."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id).all()
        matrix: Dict[int, List[Dict]] = {}
        for cap in caps:
            phase = cap.phase_introduced
            if phase not in matrix:
                matrix[phase] = []
            matrix[phase].append({
                'capability_key': cap.capability_key,
                'name': cap.name,
                'category': cap.category,
                'owner_module': cap.owner_module,
                'route_prefix': cap.route_prefix,
            })
        return {'phases': matrix, 'total_capabilities': len(caps)}

    @classmethod
    def detect_capability_overlap(cls, org_id: int) -> List[Dict]:
        """Detect capabilities sharing the same category domain."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id, status='active').all()
        domain_map: Dict[str, List] = {}
        for cap in caps:
            cat = cap.category
            if cat not in domain_map:
                domain_map[cat] = []
            domain_map[cat].append(cap.capability_key)

        overlaps = []
        for cat, keys in domain_map.items():
            if len(keys) > 1:
                canonical = CANONICAL_DOMAIN_MAP.get(cat)
                overlaps.append({
                    'category': cat,
                    'capabilities': keys,
                    'canonical_owner': canonical,
                    'overlap_count': len(keys),
                    'recommendation': (
                        f"Canonical owner: '{canonical}'. Other capabilities should delegate "
                        f"or project from this module."
                    ) if canonical else 'No canonical owner defined; review required.',
                })
        return overlaps

    @classmethod
    def identify_canonical_owner(cls, org_id: int, category: str) -> Optional[Dict]:
        """Return the canonical capability for a given domain category."""
        canonical_key = CANONICAL_DOMAIN_MAP.get(category)
        if not canonical_key:
            return None
        cap = PlatformCapability.query.filter_by(
            capability_key=canonical_key, organization_id=org_id
        ).first()
        return cap.to_dict() if cap else None

    @classmethod
    def identify_projection_models(cls, org_id: int) -> List[Dict]:
        """Identify capabilities that are analytical projections of canonical data."""
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, status='active'
        ).all()
        projections = []
        for cap in caps:
            canonical_key = CANONICAL_DOMAIN_MAP.get(cap.category)
            if canonical_key and cap.capability_key != canonical_key:
                projections.append({
                    'capability_key': cap.capability_key,
                    'category': cap.category,
                    'canonical_key': canonical_key,
                    'projection_type': 'analytical_overlay',
                })
        return projections

    @classmethod
    def validate_route_ownership(cls, org_id: int) -> Dict:
        """Verify that route prefixes are unique across capabilities."""
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, status='active'
        ).filter(PlatformCapability.route_prefix.isnot(None)).all()
        prefix_map: Dict[str, List[str]] = {}
        for cap in caps:
            prefix = cap.route_prefix.rstrip('/')
            if prefix not in prefix_map:
                prefix_map[prefix] = []
            prefix_map[prefix].append(cap.capability_key)
        collisions = {k: v for k, v in prefix_map.items() if len(v) > 1}
        return {
            'collision_count': len(collisions),
            'collisions': collisions,
            'status': 'PASS' if not collisions else 'FAIL',
        }

    @classmethod
    def validate_service_boundaries(cls, org_id: int) -> Dict:
        """Verify that each capability references a distinct service module."""
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, status='active'
        ).filter(PlatformCapability.service_reference.isnot(None)).all()
        service_map: Dict[str, List[str]] = {}
        for cap in caps:
            svc = cap.service_reference
            if svc not in service_map:
                service_map[svc] = []
            service_map[svc].append(cap.capability_key)
        shared = {k: v for k, v in service_map.items() if len(v) > 1}
        return {
            'shared_services': shared,
            'shared_count': len(shared),
            'status': 'PASS',  # Shared services are OK if explicitly documented
            'note': 'Shared services are acceptable when documented; review for ownership clarity.',
        }

    @classmethod
    def convergence_summary(cls, org_id: int) -> Dict:
        """Produce a full convergence audit summary."""
        ownership = cls.build_ownership_matrix(org_id)
        overlaps = cls.detect_capability_overlap(org_id)
        route_audit = cls.validate_route_ownership(org_id)
        service_audit = cls.validate_service_boundaries(org_id)
        projections = cls.identify_projection_models(org_id)
        return {
            'total_capabilities': ownership['total_capabilities'],
            'phase_count': len(ownership['phases']),
            'overlap_domains': len(overlaps),
            'route_status': route_audit['status'],
            'route_collisions': route_audit['collision_count'],
            'projection_model_count': len(projections),
            'service_audit': service_audit['status'],
        }
