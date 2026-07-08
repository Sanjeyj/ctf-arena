from app.models.user import User
from app.models.team import Team
from app.models.category import Category
from app.models.challenge import Challenge
from app.models.challenge_file import ChallengeFile
from app.models.flag import Flag
from app.models.hint import Hint, HintUnlock
from app.models.submission import Submission
from app.models.competition import Competition
from app.models.announcement import Announcement
from app.models.notification import Notification
from app.models.certificate import Certificate
from app.models.theme import Theme
from app.models.plugin import Plugin
from app.models.audit import AuditLog
from app.models.setting import Setting
from app.models.tag import Tag, ChallengeTag
from app.models.role import Role, Permission, UserRole, RolePermission
from app.models.login_history import LoginHistory
from app.models.docker_image import DockerImage
from app.models.deployment_profile import DeploymentProfile
from app.models.challenge_instance import ChallengeInstance
from app.models.container_log import ContainerLog
from app.models.instance_snapshot import InstanceSnapshot
from app.models.plugin_installation import PluginInstallation
from app.models.plugin_permission import PluginPermission
from app.models.plugin_setting import PluginSetting
from app.models.ai_hint_request import AIHintRequest
from app.models.ai_writeup import AIWriteup
from app.models.ai_difficulty_prediction import AIDifficultyPrediction
from app.models.ai_conversation import AIConversation

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.organization_setting import OrganizationSetting
from app.models.organization_billing import OrganizationBilling
from app.models.organization_audit_log import OrganizationAuditLog

from app.models.attack_simulation import AttackSimulation
from app.models.attack_event import AttackEvent
from app.models.defense_action import DefenseAction
from app.models.incident import Incident
from app.models.mitre_technique import MitreTechnique
from app.models.attack_chain import AttackChain

# Phase 17 — LMS & Certification Platform
from app.models.course import Course
from app.models.module import CourseModule
from app.models.lesson import Lesson
from app.models.course_enrollment import CourseEnrollment
from app.models.course_progress import CourseProgress
from app.models.learning_path import LearningPath, PathEnrollment
from app.models.badge import Badge, UserBadge
from app.models.skill import Skill, UserSkill
from app.models.career import Job, Employer, Resume

# Phase 18 — Enterprise SOC & Threat Intelligence
from app.models.ioc import IOC
from app.models.threat_feed import ThreatFeed
from app.models.sigma_rule import SigmaRule
from app.models.yara_rule import YaraRule
from app.models.alert import Alert
from app.models.detection import Detection
from app.models.case import Case
from app.models.hunt import Hunt

# Phase 19 — Security Research & CTI Platform
from app.models.threat_actor import ThreatActor
from app.models.campaign import Campaign
from app.models.malware_family import MalwareFamily
from app.models.malware_sample import MalwareSample
from app.models.research_report import ResearchReport
from app.models.yara_repository import YaraRepository
from app.models.sigma_repository import SigmaRepository
from app.models.attack_navigator import AttackNavigator

# Phase 20 — Global Cybersecurity Ecosystem
from app.models.program import Program
from app.models.vulnerability_report import VulnerabilityReport
from app.models.bounty_reward import BountyReward
from app.models.disclosure import Disclosure
from app.models.researcher_profile import ResearcherProfile
from app.models.marketplace_category import MarketplaceCategory
from app.models.marketplace_item import MarketplaceItem
from app.models.marketplace_purchase import MarketplacePurchase
from app.models.organization_trust import OrganizationTrust

# Phase 21 — Autonomous Security Operations Platform
from app.models.soc_agent import SocAgent
from app.models.threat_hunt_session import ThreatHuntSession
from app.models.incident_commander import IncidentCommander
from app.models.knowledge_node import KnowledgeNode
from app.models.knowledge_edge import KnowledgeEdge
from app.models.playbook import Playbook
from app.models.playbook_execution import PlaybookExecution

# Phase 22 — Cyber Defense Operating System
from app.models.security_event import SecurityEvent
from app.models.event_source import EventSource
from app.models.asset import Asset
from app.models.asset_group import AssetGroup
from app.models.asset_tag import AssetTag
from app.models.executive_report import ExecutiveReport
from app.models.knowledge_article import KnowledgeArticle
from app.models.runbook import Runbook

# Phase 23 — Security Operating System (SecOS)
from app.models.governance_framework import GovernanceFramework
from app.models.compliance_control import ComplianceControl
from app.models.audit_finding import AuditFinding
from app.models.risk_register import RiskRegister
from app.models.policy import Policy
from app.models.policy_acknowledgement import PolicyAcknowledgement
from app.models.shared_ioc import SharedIOC
from app.models.warehouse_event import WarehouseEvent
from app.models.warehouse_metric import WarehouseMetric
from app.models.digital_twin import DigitalTwin

# Phase 24 — Global Cyber Security Cloud
from app.models.cloud_region import CloudRegion
from app.models.cloud_node import CloudNode
from app.models.security_mesh import SecurityMesh
from app.models.mesh_route import MeshRoute
from app.models.threat_reputation import ThreatReputation
from app.models.agent_node import AgentNode
from app.models.resilience_score import ResilienceScore
from app.models.cloud_service import CloudService

# Phase 25 — Cyber Resilience Platform
from app.models.business_process import BusinessProcess
from app.models.disaster_recovery_plan import DisasterRecoveryPlan
from app.models.business_impact_analysis import BusinessImpactAnalysis
from app.models.crisis_event import CrisisEvent
from app.models.third_party_vendor import ThirdPartyVendor
from app.models.vendor_assessment import VendorAssessment
from app.models.insurance_policy import InsurancePolicy
from app.models.resilience_exercise import ResilienceExercise

# Phase 26 — Autonomous Cyber Enterprise
from app.models.autonomous_agent import AutonomousAgent
from app.models.agent_task import AgentTask
from app.models.autonomous_decision import AutonomousDecision
from app.models.remediation_action import RemediationAction
from app.models.compliance_monitor import ComplianceMonitor
from app.models.security_workflow import SecurityWorkflow
from app.models.enterprise_goal import EnterpriseGoal
from app.models.digital_worker import DigitalWorker

# Phase 27 — Global Security Intelligence Network
from app.models.global_threat_feed import GlobalThreatFeed
from app.models.intelligence_report import IntelligenceReport
from app.models.intelligence_source import IntelligenceSource
from app.models.prediction_model import PredictionModel
from app.models.forecast_event import ForecastEvent
from app.models.observatory_node import ObservatoryNode
from app.models.trust_network import TrustNetwork
from app.models.intelligence_graph import IntelligenceGraph

# Phase 28 — Cyber Civilization Platform
from app.models.cyber_nation import CyberNation
from app.models.defense_grid import DefenseGrid
from app.models.innovation_project import InnovationProject
from app.models.security_economy import SecurityEconomy
from app.models.workforce_profile import WorkforceProfile
from app.models.defense_alliance import DefenseAlliance
from app.models.prediction_scenario import PredictionScenario
from app.models.civilization_metric import CivilizationMetric

# Phase 29 — Global Cyber Command Center
from app.models.global_operation import GlobalOperation
from app.models.command_center import CommandCenter
from app.models.crisis_room import CrisisRoom
from app.models.war_game import WarGame
from app.models.cert_team import CertTeam
from app.models.strategic_objective import StrategicObjective
from app.models.threat_campaign_global import ThreatCampaignGlobal
from app.models.command_metric import CommandMetric

# Phase 30 — Unified Cyber Defense Universe
from app.models.defense_universe import DefenseUniverse
from app.models.defense_domain import DefenseDomain
from app.models.universe_node import UniverseNode
from app.models.universe_link import UniverseLink
from app.models.universe_scenario import UniverseScenario
from app.models.universe_simulation import UniverseSimulation
from app.models.universe_event import UniverseEvent
from app.models.universe_metric import UniverseMetric

# Phase 31 — Cyber Platform Control Plane
from app.models.platform_service import PlatformService
from app.models.service_dependency import ServiceDependency
from app.models.reliability_objective import ReliabilityObjective
from app.models.platform_feature_flag import PlatformFeatureFlag
from app.models.control_policy import ControlPolicy
from app.models.model_governance_record import ModelGovernanceRecord
from app.models.evidence_record import EvidenceRecord
from app.models.change_record import ChangeRecord

# Phase 32 — Cyber Trust, Assurance & Verification Fabric
from app.models.trust_identity import TrustIdentity
from app.models.device_posture import DevicePosture
from app.models.trust_decision import TrustDecision
from app.models.assurance_case import AssuranceCase
from app.models.assurance_evidence_link import AssuranceEvidenceLink
from app.models.software_attestation import SoftwareAttestation
from app.models.sbom_record import SBOMRecord
from app.models.control_validation import ControlValidation

# Phase 33 — Cyber Platform Observability, Reliability & Operations Fabric
from app.models.telemetry_source import TelemetrySource
from app.models.telemetry_metric import TelemetryMetric
from app.models.trace_record import TraceRecord
from app.models.service_health_snapshot import ServiceHealthSnapshot
from app.models.error_budget_record import ErrorBudgetRecord
from app.models.operational_incident import OperationalIncident
from app.models.chaos_experiment import ChaosExperiment
from app.models.operations_timeline_event import OperationsTimelineEvent

# Phase 34 — Security Architecture, Exposure & Attack Surface Management Fabric
from app.models.architecture_zone import ArchitectureZone
from app.models.trust_boundary import TrustBoundary
from app.models.exposure_asset import ExposureAsset
from app.models.exposure_finding import ExposureFinding
from app.models.attack_path import AttackPath
from app.models.control_coverage_map import ControlCoverageMap
from app.models.remediation_plan import RemediationPlan
from app.models.architecture_review import ArchitectureReview

# Phase 35 — Continuous Security Validation & Defense Effectiveness Fabric
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
from app.models.validation_check import ValidationCheck
from app.models.detection_validation import DetectionValidation
from app.models.playbook_readiness import PlaybookReadiness
from app.models.defense_effectiveness_metric import DefenseEffectivenessMetric
from app.models.validation_regression import ValidationRegression

# Phase 36 — Cyber Risk Quantification, Loss Modeling & Security Investment Optimization Fabric
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_frequency_estimate import RiskFrequencyEstimate
from app.models.loss_magnitude_estimate import LossMagnitudeEstimate
from app.models.risk_simulation_run import RiskSimulationRun
from app.models.risk_treatment_option import RiskTreatmentOption
from app.models.security_investment import SecurityInvestment
from app.models.risk_appetite_profile import RiskAppetiteProfile
from app.models.risk_portfolio_metric import RiskPortfolioMetric

# Phase 37 — Cyber Resilience Investment Planning, Scenario Stress Testing & Strategic Risk Decision Fabric
from app.models.stress_test_scenario import StressTestScenario
from app.models.stress_test_run import StressTestRun
from app.models.resilience_investment_plan import ResilienceInvestmentPlan
from app.models.investment_plan_item import InvestmentPlanItem
from app.models.control_investment_option import ControlInvestmentOption
from app.models.business_dependency_risk import BusinessDependencyRisk
from app.models.strategic_decision_record import StrategicDecisionRecord
from app.models.resilience_portfolio_metric import ResiliencePortfolioMetric

# Phase 38 — Enterprise Security Decision Intelligence,
# Adaptive Policy Optimization & Governance Fabric
from app.models.decision_context import DecisionContext
from app.models.decision_recommendation import DecisionRecommendation
from app.models.policy_optimization_run import PolicyOptimizationRun
from app.models.policy_conflict import PolicyConflict
from app.models.governance_objective import GovernanceObjective
from app.models.governance_scorecard import GovernanceScorecard
from app.models.decision_outcome import DecisionOutcome
from app.models.governance_drift_record import GovernanceDriftRecord



# Phase 39 - Systemic Cyber Risk, Collective Resilience
# & Federated Governance Fabric
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency
from app.models.contagion_scenario import ContagionScenario
from app.models.contagion_simulation_run import ContagionSimulationRun
from app.models.contagion_event import ContagionEvent
from app.models.collective_resilience_plan import CollectiveResiliencePlan
from app.models.mutual_aid_simulation import MutualAidSimulation
from app.models.federation_governance_record import FederationGovernanceRecord

# Phase 40 — Platform Convergence, Certification,
# Mission Control & Release Readiness
from app.models.platform_capability import PlatformCapability
from app.models.capability_dependency import CapabilityDependency
from app.models.platform_certification_run import PlatformCertificationRun
from app.models.certification_check import CertificationCheck
from app.models.release_baseline import ReleaseBaseline
from app.models.architecture_decision_record import ArchitectureDecisionRecord
from app.models.platform_readiness_metric import PlatformReadinessMetric
from app.models.release_gate_decision import ReleaseGateDecision
