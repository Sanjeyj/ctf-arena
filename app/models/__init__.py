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

