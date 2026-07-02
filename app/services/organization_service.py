from app.extensions import db
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.organization_setting import OrganizationSetting
from app.models.organization_audit_log import OrganizationAuditLog
from app.models.user import User
from app.services.billing_service import BillingService
import datetime

class OrganizationService:
    @staticmethod
    def create_org(name: str, slug: str, owner: User) -> tuple[Organization, str]:
        """Create a new organization, setup initial billing, and assign the owner."""
        slug = slug.strip().lower()
        if not slug:
            return None, "Slug cannot be empty."
        
        # Check slug uniqueness
        existing = Organization.query.filter_by(slug=slug, is_deleted=False).first()
        if existing:
            return None, f"Organization slug '{slug}' is already taken."

        org = Organization(
            name=name,
            slug=slug,
            owner_id=owner.id,
            plan_type='free',
            status='active'
        )
        db.session.add(org)
        db.session.flush()  # Get org ID

        # Set owner of user to this org
        owner.organization_id = org.id

        # Setup Billing
        BillingService.get_billing(org)

        # Add Owner to Members
        member = OrganizationMember(
            organization_id=org.id,
            user_id=owner.id,
            role='owner',
            joined_at=datetime.datetime.utcnow()
        )
        db.session.add(member)

        # Log audit
        audit = OrganizationAuditLog(
            organization_id=org.id,
            user_id=owner.id,
            action='org_created',
            resource_type='organization',
            resource_id=org.id
        )
        db.session.add(audit)

        db.session.commit()
        return org, None

    @staticmethod
    def invite_member(org: Organization, user: User, role: str, actor_id: int = None) -> tuple[OrganizationMember, str]:
        """Invite/Add a user to an organization."""
        if role not in ('owner', 'administrator', 'manager', 'instructor', 'member', 'read_only'):
            return None, "Invalid role."

        # Check if already a member
        existing = OrganizationMember.query.filter_by(organization_id=org.id, user_id=user.id).first()
        if existing:
            return None, "User is already a member of this organization."

        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=role,
            invited_by=actor_id,
            joined_at=datetime.datetime.utcnow()
        )
        # Associate user's organization_id to this org
        user.organization_id = org.id
        db.session.add(member)

        # Log audit
        audit = OrganizationAuditLog(
            organization_id=org.id,
            user_id=actor_id,
            action='member_invited',
            resource_type='user',
            resource_id=user.id
        )
        audit.details = {'invited_role': role}
        db.session.add(audit)

        db.session.commit()
        return member, None

    @staticmethod
    def change_role(member: OrganizationMember, new_role: str, actor_id: int = None) -> tuple[bool, str]:
        """Change a member's role."""
        if new_role not in ('owner', 'administrator', 'manager', 'instructor', 'member', 'read_only'):
            return False, "Invalid role."

        old_role = member.role
        member.role = new_role

        audit = OrganizationAuditLog(
            organization_id=member.organization_id,
            user_id=actor_id,
            action='member_role_changed',
            resource_type='user',
            resource_id=member.user_id
        )
        audit.details = {'old_role': old_role, 'new_role': new_role}
        db.session.add(audit)

        db.session.commit()
        return True, None

    @staticmethod
    def remove_member(member: OrganizationMember, actor_id: int = None) -> tuple[bool, str]:
        """Remove a member from the organization."""
        # Clean up user's organization association
        user = User.query.get(member.user_id)
        if user:
            user.organization_id = None

        org_id = member.organization_id
        user_id = member.user_id
        db.session.delete(member)

        audit = OrganizationAuditLog(
            organization_id=org_id,
            user_id=actor_id,
            action='member_removed',
            resource_type='user',
            resource_id=user_id
        )
        db.session.add(audit)

        db.session.commit()
        return True, None

    @staticmethod
    def get_members(org: Organization) -> list[OrganizationMember]:
        return OrganizationMember.query.filter_by(organization_id=org.id).all()

    @staticmethod
    def get_org_by_slug(slug: str) -> Organization:
        return Organization.query.filter_by(slug=slug.strip().lower(), is_deleted=False).first()

    @staticmethod
    def set_setting(org: Organization, key: str, value: str, actor_id: int = None):
        setting = OrganizationSetting.query.filter_by(organization_id=org.id, key=key).first()
        if setting:
            setting.value = value
        else:
            setting = OrganizationSetting(organization_id=org.id, key=key, value=value)
            db.session.add(setting)

        audit = OrganizationAuditLog(
            organization_id=org.id,
            user_id=actor_id,
            action='setting_changed',
            resource_type='setting',
            resource_id=setting.id
        )
        audit.details = {'key': key, 'value': value}
        db.session.add(audit)
        db.session.commit()
        return setting
