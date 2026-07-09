"""ExecutivePlatformAI — Phase 40: final executive briefing service.

Generates executive briefings summarizing platform maturity, certifications, release blockers, and readiness.
Reuses existing AIService, prompt injection detection, and output masking of flags and secrets.
"""
import re
from typing import Optional
from app.services.ai_service import AIService
from app.models.platform_capability import PlatformCapability
from app.models.platform_certification_run import PlatformCertificationRun
from app.models.release_baseline import ReleaseBaseline
from app.models.release_gate_decision import ReleaseGateDecision
from app.models.architecture_decision_record import ArchitectureDecisionRecord
from app.models.platform_readiness_metric import PlatformReadinessMetric

# Prompt injection pattern matching
INJECTION_PATTERNS = [
    r'ignore\s+previous',
    r'ignore\s+all',
    r'jailbreak',
    r'bypass\s+safety',
    r'act\s+as\s+.*(dan|unrestricted)',
    r'override\s+instructions',
    r'disregard\s+(all|previous)',
]

# Masking patterns for secrets and CTF flags
SECRET_PATTERNS = [
    (re.compile(r'CTF\{[^}]+\}', re.IGNORECASE), '[CTF_FLAG_REDACTED]'),
    (re.compile(r'flag\{[^}]+\}', re.IGNORECASE), '[CTF_FLAG_REDACTED]'),
    (re.compile(r'(password|secret|token|api[_-]key)[=:]\s*\S+', re.IGNORECASE), r'\1=[REDACTED]'),
    (re.compile(r'Bearer\s+\S+', re.IGNORECASE), 'Bearer [REDACTED]'),
]


class ExecutivePlatformAI:
    """Safe executive platform briefings generator using AIService."""

    @staticmethod
    def _sanitize(prompt: str) -> str:
        """Detect and block prompt injection attempts."""
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise ValueError(f"Prompt injection detected: pattern '{pattern}' matched")
        return prompt

    @staticmethod
    def _mask_secrets(text: str) -> str:
        """Mask secrets and CTF flags in AI response."""
        for pattern, replacement in SECRET_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    @staticmethod
    def _generate(prompt: str) -> str:
        """Safe wrapper around AIService.generate with injection checks and masking."""
        sanitized = ExecutivePlatformAI._sanitize(prompt)
        raw = AIService.generate(sanitized)
        # raw is tuple (text, tokens, provider)
        return ExecutivePlatformAI._mask_secrets(raw[0])

    @staticmethod
    def summarize_platform_architecture(org_id: int) -> str:
        """Generate executive summary of platform architecture convergence."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id).count()
        adrs = ArchitectureDecisionRecord.query.filter_by(organization_id=org_id).count()
        prompt = (
            f"You are a lead platform architect. Summarize the converged cyber defense "
            f"platform architecture: {caps} capability registry entries registered, "
            f"{adrs} architecture decision records. Discuss convergence, "
            f"modular boundaries, and architectural health. Be concise."
        )
        return ExecutivePlatformAI._generate(prompt)

    @staticmethod
    def summarize_certification_status(org_id: int) -> str:
        """Generate summary of latest platform certification runs."""
        run = PlatformCertificationRun.query.filter_by(organization_id=org_id).order_by(
            PlatformCertificationRun.created_at.desc()
        ).first()
        if not run:
            return "No platform certification runs recorded."
        prompt = (
            f"Summarize the platform certification run status: "
            f"Name: {run.name}, Type: {run.certification_type}, Status: {run.status}, "
            f"Overall Score: {run.overall_score:.1f}/100 if run.overall_score is not None else 0.0. "
            f"Include assessments for Security ({run.security_score}), "
            f"Tenant Isolation ({run.tenant_isolation_score}), AI Safety ({run.ai_safety_score}), "
            f"and Reliability ({run.reliability_score})."
        )
        return ExecutivePlatformAI._generate(prompt)

    @staticmethod
    def explain_release_blockers(org_id: int) -> str:
        """Generate summary of active release blockers based on failed gate decisions."""
        gates = ReleaseGateDecision.query.filter_by(organization_id=org_id, decision='fail').all()
        if not gates:
            return "No active release blockers identified. All evaluated release gates are passing."
        blockers_summary = ", ".join([f"{g.gate_type} ({g.reason})" for g in gates])
        prompt = (
            f"As a platform release manager, explain the following active release blockers: "
            f"{blockers_summary}. Outline immediate priorities for structural resolution. Be concise."
        )
        return ExecutivePlatformAI._generate(prompt)

    @staticmethod
    def recommend_readiness_priorities(org_id: int) -> str:
        """AI recommendations for improving platform readiness scores."""
        metric = PlatformReadinessMetric.query.filter_by(organization_id=org_id).order_by(
            PlatformReadinessMetric.measured_at.desc()
        ).first()
        if not metric:
            return "No readiness metrics recorded yet. Trigger a readiness evaluation."
        prompt = (
            f"Recommend improvement priorities based on current platform readiness scores: "
            f"Overall: {metric.overall_readiness_score:.1f}/100, "
            f"Security: {metric.security_score:.1f}, Reliability: {metric.reliability_score:.1f}, "
            f"Governance: {metric.governance_score:.1f}, Resilience: {metric.resilience_score:.1f}, "
            f"Assurance: {metric.assurance_score:.1f}, Operations: {metric.operations_score:.1f}. "
            f"Identify the lowest scoring categories and propose targeted improvements."
        )
        return ExecutivePlatformAI._generate(prompt)

    @staticmethod
    def summarize_cross_phase_risk(org_id: int) -> str:
        """Briefing on cross-phase risk profile (operational, systemic, regulatory)."""
        prompt = (
            f"Provide an executive briefing on the platform's cross-phase risk profile. "
            f"Outline how systemic dependencies map to tenant-isolation and AI safety "
            f"boundaries. Keep the analysis strictly strategic."
        )
        return ExecutivePlatformAI._generate(prompt)

    @staticmethod
    def explain_capability_dependencies(org_id: int) -> str:
        """AI narrative on capability dependency structure and criticality."""
        caps = PlatformCapability.query.filter_by(organization_id=org_id).count()
        prompt = (
            f"Explain the capability dependency structure of the platform: {caps} total "
            f"modules registered. Highlight single-point-of-failure risks and coupling "
            f"management strategies."
        )
        return ExecutivePlatformAI._generate(prompt)

    @staticmethod
    def generate_final_platform_brief(org_id: int) -> str:
        """Generate final platform release readiness brief."""
        metric = PlatformReadinessMetric.query.filter_by(organization_id=org_id).order_by(
            PlatformReadinessMetric.measured_at.desc()
        ).first()
        bl = ReleaseBaseline.query.filter_by(organization_id=org_id).first()
        ver = bl.version if bl else "v0.0.0"
        score = metric.overall_readiness_score if metric else 0.0

        prompt = (
            f"Generate a final platform release readiness executive briefing for version {ver}. "
            f"Readiness Score: {score:.1f}/100. Provide a summary of the converged cyber "
            f"defense posture, certs, and release readiness status. Be professional, "
            f"strategic, and concise."
        )
        return ExecutivePlatformAI._generate(prompt)
