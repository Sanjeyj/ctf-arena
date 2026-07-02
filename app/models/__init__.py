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




