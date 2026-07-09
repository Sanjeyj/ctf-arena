"""Phase 40 — Capability Registry Service.

Manages the canonical registry of platform capabilities.
All operations are offline, simulation-only, and tenant-isolated.
"""
import logging
from typing import Dict, List, Optional

from app.extensions import db
from app.models.platform_capability import PlatformCapability
from app.models.capability_dependency import CapabilityDependency

logger = logging.getLogger(__name__)


class CapabilityRegistryService:
    """Manages the canonical capability registry and dependency graph."""

    # Pre-seeded Phase → Capability inventory for auto-discovery
    PHASE_CAPABILITIES = [
        # (key, name, phase, category, module, service_ref, route_prefix)
        ('ctf_challenges', 'CTF Challenges', 1, 'platform', 'challenges', 'challenge_service', '/api/v1/challenges'),
        ('soc_platform', 'SOC Platform', 5, 'operations', 'soc', 'soc_ai_service', '/api/v1/soc'),
        ('lms_platform', 'LMS Platform', 17, 'platform', 'lms', 'skill_service', '/api/v1/lms'),
        ('cloud_platform', 'Cloud Security Platform', 21, 'platform', 'cloud', 'cloud_service_manager', '/api/v1/cloud'),
        ('grc_platform', 'GRC & Compliance Platform', 22, 'governance', 'enterprise', 'compliance_monitor_service', '/api/v1/enterprise'),
        ('cyber_resilience', 'Cyber Resilience Platform', 24, 'resilience', 'resilience', 'resilience_engine_service', '/api/v1/resilience'),
        ('cyber_intelligence', 'Cyber Intelligence Platform', 26, 'intelligence', 'intelligence', 'threat_intelligence_service', '/api/v1/intelligence'),
        ('cyber_civilization', 'Cyber Civilization Platform', 27, 'simulation', 'civilization', 'civilization_service', '/api/v1/civilization'),
        ('global_command', 'Global Cyber Command', 28, 'operations', 'command', 'command_service', '/api/v1/command'),
        ('defense_universe', 'Unified Cyber Defense Universe', 30, 'simulation', 'universe', 'universe_service', '/api/v1/universe'),
        ('control_plane', 'Cyber Platform Control Plane', 31, 'platform', 'control_plane', 'control_policy_service', '/api/v1/control-plane'),
        ('trust_assurance', 'Cyber Trust & Assurance Fabric', 32, 'trust', 'assurance', 'assurance_service', '/api/v1/assurance'),
        ('observability_fabric', 'Observability, Reliability & Operations Fabric', 33, 'observability', 'operations', 'telemetry_service', '/api/v1/operations'),
        ('exposure_fabric', 'Security Architecture & Exposure Fabric', 34, 'exposure', 'exposure', 'exposure_inventory_service', '/api/v1/exposure'),
        ('validation_fabric', 'Continuous Security Validation Fabric', 35, 'validation', 'validation_fabric', 'validation_engine_service', '/api/v1/validation'),
        ('risk_quantification', 'Cyber Risk Quantification Fabric', 36, 'risk', 'risk_quantification', 'risk_scenario_service', '/api/v1/risk-quantification'),
        ('strategic_resilience', 'Strategic Resilience & Decision Fabric', 37, 'resilience', 'strategic_resilience', 'resilience_planning_service', '/api/v1/strategic-resilience'),
        ('governance_intelligence', 'Enterprise Governance Intelligence Fabric', 38, 'governance', 'governance_intelligence', 'decision_intelligence_service', '/api/v1/governance-intelligence'),
        ('systemic_resilience', 'Systemic Cyber Risk & Resilience Fabric', 39, 'resilience', 'systemic_resilience', 'systemic_risk_graph_service', '/api/v1/systemic-resilience'),
        ('mission_control', 'Platform Mission Control & Certification', 40, 'certification', 'mission_control', 'platform_certification_service', '/api/v1/mission-control'),
    ]

    @classmethod
    def discover_capabilities(cls, org_id: int) -> List[Dict]:
        """Return all capabilities registered for the given tenant."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id).all()
        return [c.to_dict() for c in caps]

    @classmethod
    def register_capability(
        cls,
        org_id: int,
        capability_key: str,
        name: str,
        phase_introduced: int,
        category: str = 'platform',
        description: str = '',
        owner_module: str = '',
        service_reference: str = '',
        route_prefix: str = '',
        maturity_score: float = 50.0,
    ) -> Dict:
        """Register or update a capability in the tenant registry."""
        if not capability_key or not name:
            raise ValueError("capability_key and name are required")
        if not 0.0 <= maturity_score <= 100.0:
            raise ValueError("maturity_score must be in [0, 100]")

        existing = PlatformCapability.query.filter_by(
            capability_key=capability_key, organization_id=org_id
        ).first()

        if existing:
            existing.name = name
            existing.phase_introduced = phase_introduced
            existing.category = category
            existing.description = description
            existing.owner_module = owner_module
            existing.service_reference = service_reference
            existing.route_prefix = route_prefix
            existing.maturity_score = min(100.0, max(0.0, maturity_score))
            db.session.commit()
            return existing.to_dict()

        cap = PlatformCapability(
            capability_key=capability_key,
            name=name,
            phase_introduced=phase_introduced,
            category=category,
            description=description,
            owner_module=owner_module,
            service_reference=service_reference,
            route_prefix=route_prefix,
            maturity_score=min(100.0, max(0.0, maturity_score)),
            status='active',
            organization_id=org_id,
        )
        db.session.add(cap)
        db.session.commit()
        logger.info(f"[CapabilityRegistry] Registered capability '{capability_key}' for org {org_id}")
        return cap.to_dict()

    @classmethod
    def update_maturity(cls, org_id: int, capability_id: int, maturity_score: float) -> Dict:
        """Update maturity score for a capability; clamped to [0, 100]."""
        cap = PlatformCapability.query.filter_by(id=capability_id, organization_id=org_id).first()
        if not cap:
            raise ValueError(f"Capability {capability_id} not found for org {org_id}")
        cap.maturity_score = min(100.0, max(0.0, maturity_score))
        db.session.commit()
        return cap.to_dict()

    @classmethod
    def build_dependency_map(cls, org_id: int) -> Dict:
        """Build adjacency map of capability dependencies for the tenant."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id).all()
        cap_index = {c.id: c.capability_key for c in caps}
        deps = CapabilityDependency.query.filter_by(organization_id=org_id, status='active').all()
        adj: Dict[str, List[str]] = {c.capability_key: [] for c in caps}
        for dep in deps:
            src_key = cap_index.get(dep.source_capability_id)
            tgt_key = cap_index.get(dep.target_capability_id)
            if src_key and tgt_key:
                adj[src_key].append(tgt_key)
        return {'adjacency': adj, 'edge_count': len(deps), 'node_count': len(caps)}

    @classmethod
    def validate_dependency(
        cls,
        org_id: int,
        source_id: int,
        target_id: int,
    ) -> Dict:
        """Validate that a dependency edge is acceptable."""
        errors = []
        if source_id == target_id:
            errors.append("Self-edge rejected: source and target must differ")
        src = PlatformCapability.query.filter_by(id=source_id, organization_id=org_id).first()
        tgt = PlatformCapability.query.filter_by(id=target_id, organization_id=org_id).first()
        if not src:
            errors.append(f"Source capability {source_id} not found for org {org_id}")
        if not tgt:
            errors.append(f"Target capability {target_id} not found for org {org_id}")
        if src and tgt:
            existing = CapabilityDependency.query.filter_by(
                source_capability_id=source_id,
                target_capability_id=target_id,
                organization_id=org_id,
                status='active',
            ).first()
            if existing:
                errors.append("Duplicate active dependency already exists")
        return {'valid': len(errors) == 0, 'errors': errors}

    @classmethod
    def find_critical_capabilities(cls, org_id: int, threshold: float = 70.0) -> List[Dict]:
        """Find capabilities with many incoming dependencies or high coupling."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id, status='active').all()
        critical = []
        for cap in caps:
            in_count = CapabilityDependency.query.filter_by(
                target_capability_id=cap.id, organization_id=org_id, status='active'
            ).count()
            if in_count >= 3 or (cap.maturity_score is not None and cap.maturity_score < threshold):
                d = cap.to_dict()
                d['incoming_dependency_count'] = in_count
                critical.append(d)
        return critical

    @classmethod
    def capability_summary(cls, org_id: int) -> Dict:
        """Return aggregate summary of capability registry state."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id).all()
        active = [c for c in caps if c.status == 'active']
        dep_count = CapabilityDependency.query.filter_by(organization_id=org_id, status='active').count()
        scores = [c.maturity_score for c in active if c.maturity_score is not None]
        avg_maturity = round(sum(scores) / len(scores), 4) if scores else 0.0
        categories = {}
        for cap in active:
            categories[cap.category] = categories.get(cap.category, 0) + 1
        return {
            'total_capabilities': len(caps),
            'active_capabilities': len(active),
            'active_dependencies': dep_count,
            'avg_maturity_score': avg_maturity,
            'categories': categories,
        }
