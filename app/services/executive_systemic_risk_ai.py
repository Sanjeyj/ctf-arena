"""
ExecutiveSystemicRiskAI — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Generates executive-level AI briefings about systemic risk and collective resilience.
Reuses existing AIService, StubProvider, prompt sanitization, and secret masking.
Does NOT create new AI providers or bypass existing safety controls.
"""
import re
from app.services.ai_service import AIService
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency
from app.models.contagion_simulation_run import ContagionSimulationRun
from app.models.collective_resilience_plan import CollectiveResiliencePlan
from app.models.mutual_aid_simulation import MutualAidSimulation
from app.models.federation_governance_record import FederationGovernanceRecord
from app.services.ecosystem_resilience_service import EcosystemResilienceService

# Prompt injection patterns — reuse of existing safety patterns
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


class ExecutiveSystemicRiskAI:

    @staticmethod
    def _sanitize(prompt: str) -> str:
        """Detect and block prompt injection attempts."""
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise ValueError(f"Prompt injection detected: pattern '{pattern}' matched")
        return prompt

    @staticmethod
    def _mask_secrets(text: str) -> str:
        """Mask secrets and CTF flags in AI output."""
        for pattern, replacement in SECRET_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    @staticmethod
    def _generate(prompt: str) -> str:
        """Safe wrapper around AIService.generate with masking."""
        sanitized = ExecutiveSystemicRiskAI._sanitize(prompt)
        raw = AIService.generate(sanitized)
        return ExecutiveSystemicRiskAI._mask_secrets(raw[0])

    @staticmethod
    def summarize_systemic_risk(org_id):
        """Generate executive summary of systemic risk posture."""
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).count()
        deps = SystemicDependency.query.filter_by(organization_id=org_id).count()
        summary = EcosystemResilienceService.save_metrics(org_id)
        prompt = (
            f"You are a systemic risk executive analyst. Summarize the systemic risk posture: "
            f"{nodes} risk nodes, {deps} dependencies, systemic risk index "
            f"{summary['systemic_risk_index']:.1f}/100, composite resilience "
            f"{summary['composite_resilience']:.1f}/100. Provide a concise executive summary."
        )
        return ExecutiveSystemicRiskAI._generate(prompt)

    @staticmethod
    def explain_contagion_path(run_id, org_id):
        """Generate explanation of a contagion simulation run."""
        run = ContagionSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return "No simulation run found."
        prompt = (
            f"Explain the following contagion simulation result in executive terms: "
            f"{run.nodes_affected} nodes affected, maximum propagation depth "
            f"{run.maximum_depth_reached}, aggregate impact score "
            f"{run.aggregate_impact_score:.1f}/100, collective resilience "
            f"{run.collective_resilience_score:.1f}/100, estimated recovery "
            f"{run.estimated_recovery_hours:.1f} hours."
        )
        return ExecutiveSystemicRiskAI._generate(prompt)

    @staticmethod
    def identify_concentration_risk(org_id):
        """AI narrative about concentration risk points."""
        deps = SystemicDependency.query.filter_by(organization_id=org_id).count()
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).count()
        prompt = (
            f"As a systemic risk analyst, identify concentration risk factors given "
            f"{nodes} nodes and {deps} dependency edges. Describe which node types "
            f"represent the greatest single-point-of-failure risk. Be concise."
        )
        return ExecutiveSystemicRiskAI._generate(prompt)

    @staticmethod
    def recommend_collective_resilience_priorities(org_id):
        """AI recommendation on collective resilience investment priorities."""
        plans = CollectiveResiliencePlan.query.filter_by(organization_id=org_id).count()
        approved = CollectiveResiliencePlan.query.filter_by(
            organization_id=org_id, approval_status='approved'
        ).count()
        prompt = (
            f"Recommend collective resilience investment priorities given "
            f"{plans} total plans with {approved} approved. "
            f"Focus on systemic risk reduction and mutual dependency diversification."
        )
        return ExecutiveSystemicRiskAI._generate(prompt)

    @staticmethod
    def summarize_mutual_aid_simulation(org_id):
        """AI summary of simulated mutual aid allocations."""
        aids = MutualAidSimulation.query.filter_by(organization_id=org_id).count()
        approved = MutualAidSimulation.query.filter_by(
            organization_id=org_id, approval_status='approved'
        ).count()
        prompt = (
            f"Summarize the simulated mutual aid landscape: {aids} total allocations, "
            f"{approved} approved. Explain the collective recovery benefit."
        )
        return ExecutiveSystemicRiskAI._generate(prompt)

    @staticmethod
    def explain_federation_decision(record_id, org_id):
        """AI explanation of a specific federation governance decision."""
        record = FederationGovernanceRecord.query.filter_by(
            id=record_id, organization_id=org_id
        ).first()
        if not record:
            return "No federation governance record found."
        prompt = (
            f"Explain the following federation governance decision in executive terms: "
            f"'{record.title}' of type '{record.decision_type}'. Status: "
            f"{record.decision_status}. Consensus score: {record.consensus_score:.1f}/100. "
            f"Systemic risk impact: {record.systemic_risk_impact:+.1f}."
        )
        return ExecutiveSystemicRiskAI._generate(prompt)

    @staticmethod
    def generate_systemic_risk_brief(org_id):
        """Generate a comprehensive executive systemic risk brief."""
        metrics = EcosystemResilienceService.save_metrics(org_id)
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).count()
        runs = ContagionSimulationRun.query.filter_by(
            organization_id=org_id, status='completed'
        ).count()
        prompt = (
            f"Generate a comprehensive executive systemic cyber risk brief: "
            f"{nodes} ecosystem nodes, {runs} completed contagion simulations. "
            f"Systemic risk index: {metrics['systemic_risk_index']:.1f}/100. "
            f"Composite resilience: {metrics['composite_resilience']:.1f}/100. "
            f"Dependency resilience: {metrics['dependency_resilience']:.1f}, "
            f"sector: {metrics['sector_resilience']:.1f}, "
            f"regional: {metrics['regional_resilience']:.1f}. "
            f"Include top priorities and recommended actions."
        )
        return ExecutiveSystemicRiskAI._generate(prompt)
