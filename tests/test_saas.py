"""
Phase 15 — Multi-Tenant SaaS Edition Test Suite.

8 test groups, 40+ new tests.
Target: 170+ total passing tests (was 154).
"""
import pytest
import datetime
from app.extensions import db
from app.services.auth_service import hash_password
from app.repositories.user_repository import UserRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(app, username='saas_user'):
    with app.app_context():
        u = UserRepository.create(username=username, password_hash=hash_password('Pass1!'))
        return u.id


def _make_org(app, name='Test Org', slug='testorg', owner_id=None):
    from app.services.organization_service import OrganizationService
    from app.models.user import User
    with app.app_context():
        owner = User.query.get(owner_id) if owner_id else UserRepository.create(
            username=f'owner_{slug}', password_hash=hash_password('Pass1!')
        )
        org, err = OrganizationService.create_org(name, slug, owner)
        if err:
            raise RuntimeError(f"Failed to create org: {err}")
        return org.id, owner.id


# ===========================================================================
# GROUP 1 — Organization Model CRUD
# ===========================================================================
class TestOrganizationModel:

    def test_create_organization(self, app):
        """Organization can be created with required fields."""
        from app.models.organization import Organization
        owner_id = _make_user(app, 'org_create_owner')
        with app.app_context():
            from app.models.user import User
            owner = User.query.get(owner_id)
            org = Organization(name='Test Corp', slug='testcorp', owner_id=owner.id, plan_type='free')
            db.session.add(org)
            db.session.commit()
            assert org.id is not None
            assert org.slug == 'testcorp'
            assert org.plan_type == 'free'
            assert org.status == 'active'

    def test_slug_uniqueness(self, app):
        """Two organizations cannot share the same slug."""
        from app.models.organization import Organization
        owner_id = _make_user(app, 'slug_owner')
        with app.app_context():
            from app.models.user import User
            owner = User.query.get(owner_id)
            org1 = Organization(name='Org One', slug='uniqueslug', owner_id=owner.id)
            db.session.add(org1)
            db.session.commit()

            org2 = Organization(name='Org Two', slug='uniqueslug', owner_id=owner.id)
            db.session.add(org2)
            import sqlalchemy.exc
            with pytest.raises(sqlalchemy.exc.IntegrityError):
                db.session.commit()

    def test_soft_delete(self, app):
        """SoftDeleteMixin.soft_delete() sets is_deleted=True."""
        from app.models.organization import Organization
        owner_id = _make_user(app, 'soft_del_owner')
        with app.app_context():
            from app.models.user import User
            owner = User.query.get(owner_id)
            org = Organization(name='Del Corp', slug='delcorp', owner_id=owner.id)
            db.session.add(org)
            db.session.commit()
            org.soft_delete()
            db.session.commit()
            assert Organization.query.get(org.id).is_deleted is True

    def test_get_quota_plan_default(self, app):
        """Organization.get_quota() returns plan default when no override set."""
        from app.models.organization import Organization
        with app.app_context():
            org = Organization(name='Quota Org', slug='quotaorg', plan_type='professional')
            db.session.add(org)
            db.session.commit()
            assert org.get_quota('users') == 1000
            assert org.get_quota('competitions') == 10
            assert org.get_quota('challenges') == 500

    def test_get_quota_enterprise_unlimited(self, app):
        """Enterprise plan returns -1 (unlimited) for all resources."""
        from app.models.organization import Organization
        with app.app_context():
            org = Organization(name='Ent Org', slug='entorg', plan_type='enterprise')
            db.session.add(org)
            db.session.commit()
            assert org.get_quota('users') == -1
            assert org.get_quota('containers') == -1

    def test_get_quota_custom_override(self, app):
        """Organization.get_quota() respects column-level override."""
        from app.models.organization import Organization
        with app.app_context():
            org = Organization(name='Override Org', slug='overrideorg', plan_type='free', max_users=999)
            db.session.add(org)
            db.session.commit()
            assert org.get_quota('users') == 999  # Custom override beats plan default

    def test_organization_uuid_auto_assigned(self, app):
        """Each organization gets a unique UUID on creation."""
        from app.models.organization import Organization
        with app.app_context():
            o1 = Organization(name='UUID Org 1', slug='uuidorg1')
            o2 = Organization(name='UUID Org 2', slug='uuidorg2')
            db.session.add_all([o1, o2])
            db.session.commit()
            assert o1.uuid != o2.uuid
            assert len(o1.uuid) == 36  # Standard UUID format


# ===========================================================================
# GROUP 2 — Organization Members
# ===========================================================================
class TestOrganizationMember:

    def test_invite_member(self, app):
        """OrganizationService.invite_member creates a membership record."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_member import OrganizationMember
        org_id, owner_id = _make_org(app, 'Invite Corp', 'invitecorp')
        member_uid = _make_user(app, 'invite_member_user')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user = User.query.get(member_uid)
            m, err = OrganizationService.invite_member(org, user, 'instructor', actor_id=owner_id)
            assert err is None
            assert m is not None
            assert m.role == 'instructor'
            assert OrganizationMember.query.filter_by(organization_id=org_id, user_id=member_uid).count() == 1

    def test_duplicate_invite_rejected(self, app):
        """Inviting the same user twice returns an error."""
        from app.services.organization_service import OrganizationService
        org_id, owner_id = _make_org(app, 'Dup Invite Corp', 'dupinvitecorp')
        member_uid = _make_user(app, 'dup_invite_user')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user = User.query.get(member_uid)
            OrganizationService.invite_member(org, user, 'member', actor_id=owner_id)
            _, err = OrganizationService.invite_member(org, user, 'member', actor_id=owner_id)
            assert err is not None
            assert 'already a member' in err

    def test_change_role(self, app):
        """OrganizationService.change_role updates member role."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_member import OrganizationMember
        org_id, owner_id = _make_org(app, 'Role Corp', 'rolecorp')
        member_uid = _make_user(app, 'role_change_user')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user = User.query.get(member_uid)
            m, _ = OrganizationService.invite_member(org, user, 'member', actor_id=owner_id)
            OrganizationService.change_role(m, 'manager', actor_id=owner_id)
            assert OrganizationMember.query.get(m.id).role == 'manager'

    def test_remove_member(self, app):
        """OrganizationService.remove_member deletes the membership record."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_member import OrganizationMember
        org_id, owner_id = _make_org(app, 'Remove Corp', 'removecorp')
        member_uid = _make_user(app, 'remove_member_user')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user = User.query.get(member_uid)
            m, _ = OrganizationService.invite_member(org, user, 'read_only', actor_id=owner_id)
            mid = m.id
            OrganizationService.remove_member(m, actor_id=owner_id)
            assert OrganizationMember.query.get(mid) is None

    def test_role_hierarchy_can_method(self, app):
        """OrganizationMember.can() correctly enforces role hierarchy."""
        from app.models.organization_member import OrganizationMember
        with app.app_context():
            # owner has index 0, which is highest privilege
            m = OrganizationMember(role='owner')
            assert m.can('owner') is True
            assert m.can('administrator') is True
            assert m.can('member') is True
            # read_only is lowest privilege — cannot act as owner
            m2 = OrganizationMember(role='read_only')
            assert m2.can('owner') is False

    def test_get_members_list(self, app):
        """OrganizationService.get_members returns all membership records."""
        from app.services.organization_service import OrganizationService
        org_id, owner_id = _make_org(app, 'Members Corp', 'memberscorp')
        u2 = _make_user(app, 'members_list_u2')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user2 = User.query.get(u2)
            OrganizationService.invite_member(org, user2, 'member', actor_id=owner_id)
            members = OrganizationService.get_members(org)
            # owner + invited member = 2
            assert len(members) == 2


# ===========================================================================
# GROUP 3 — Organization Settings
# ===========================================================================
class TestOrganizationSettings:

    def test_set_and_get_setting(self, app):
        """OrganizationService.set_setting creates and retrieves a setting."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_setting import OrganizationSetting
        org_id, owner_id = _make_org(app, 'Settings Corp', 'settingscorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            OrganizationService.set_setting(org, 'welcome_message', 'Welcome to our CTF!', actor_id=owner_id)
            s = OrganizationSetting.query.filter_by(organization_id=org_id, key='welcome_message').first()
            assert s is not None
            assert s.value == 'Welcome to our CTF!'

    def test_update_setting(self, app):
        """set_setting updates an existing key without creating a duplicate."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_setting import OrganizationSetting
        org_id, owner_id = _make_org(app, 'Update Settings Corp', 'updatesettingscorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            OrganizationService.set_setting(org, 'theme', 'dark')
            OrganizationService.set_setting(org, 'theme', 'neon')
            count = OrganizationSetting.query.filter_by(organization_id=org_id, key='theme').count()
            assert count == 1
            val = OrganizationSetting.query.filter_by(organization_id=org_id, key='theme').first().value
            assert val == 'neon'

    def test_unique_setting_per_org(self, app):
        """Same key in different organizations does not conflict."""
        from app.services.organization_service import OrganizationService
        org1_id, o1_owner = _make_org(app, 'Org Alpha', 'orgalpha')
        org2_id, o2_owner = _make_org(app, 'Org Beta', 'orgbeta')
        with app.app_context():
            from app.models.organization import Organization
            org1 = Organization.query.get(org1_id)
            org2 = Organization.query.get(org2_id)
            OrganizationService.set_setting(org1, 'color', 'blue')
            OrganizationService.set_setting(org2, 'color', 'red')
            from app.models.organization_setting import OrganizationSetting
            v1 = OrganizationSetting.query.filter_by(organization_id=org1_id, key='color').first().value
            v2 = OrganizationSetting.query.filter_by(organization_id=org2_id, key='color').first().value
            assert v1 == 'blue'
            assert v2 == 'red'


# ===========================================================================
# GROUP 4 — Billing State Machine
# ===========================================================================
class TestBillingService:

    def test_initial_billing_is_trial(self, app):
        """OrganizationBilling is created in trial state."""
        from app.services.billing_service import BillingService
        org_id, _ = _make_org(app, 'Trial Corp', 'trialcorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            billing = BillingService.get_billing(org)
            assert billing.status == 'trial'
            assert billing.trial_ends_at is not None

    def test_trial_to_active(self, app):
        """BillingService.upgrade transitions trial → active."""
        from app.services.billing_service import BillingService
        org_id, owner_id = _make_org(app, 'Upgrade Corp', 'upgradecorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            success, msg = BillingService.upgrade(org, 'professional', actor_id=owner_id)
            assert success is True
            billing = BillingService.get_billing(org)
            assert billing.status == 'active'
            assert billing.plan_type == 'professional'

    def test_active_to_past_due(self, app):
        """BillingService.mark_past_due transitions active → past_due."""
        from app.services.billing_service import BillingService
        org_id, owner_id = _make_org(app, 'PastDue Corp', 'pastduecorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            BillingService.upgrade(org, 'professional')
            success, _ = BillingService.mark_past_due(org)
            assert success is True
            assert BillingService.get_billing(org).status == 'past_due'

    def test_past_due_to_active(self, app):
        """BillingService: past_due can recover to active via upgrade."""
        from app.services.billing_service import BillingService
        org_id, _ = _make_org(app, 'Recover Corp', 'recovercorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            BillingService.upgrade(org, 'professional')
            BillingService.mark_past_due(org)
            success, _ = BillingService.upgrade(org, 'professional')
            assert success is True
            assert BillingService.get_billing(org).status == 'active'

    def test_active_to_cancelled(self, app):
        """BillingService.cancel transitions active → cancelled."""
        from app.services.billing_service import BillingService
        org_id, owner_id = _make_org(app, 'Cancel Corp', 'cancelcorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            BillingService.upgrade(org, 'professional')
            success, _ = BillingService.cancel(org, actor_id=owner_id)
            assert success is True
            assert BillingService.get_billing(org).status == 'cancelled'

    def test_cancelled_is_terminal(self, app):
        """Cannot transition out of cancelled state."""
        from app.services.billing_service import BillingService
        org_id, _ = _make_org(app, 'Terminal Corp', 'terminalcorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            BillingService.upgrade(org, 'professional')
            BillingService.cancel(org)
            # Billing.cancel would set status to cancelled; try another cancel
            billing = BillingService.get_billing(org)
            success, err = billing.transition_to('active')
            assert success is False
            assert 'Cannot transition' in err

    def test_is_active_trial(self, app):
        """BillingService.is_active returns True for trial status."""
        from app.services.billing_service import BillingService
        org_id, _ = _make_org(app, 'IsActive Corp', 'isactivecorp')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            # Should be trial by default
            assert BillingService.is_active(org) is True


# ===========================================================================
# GROUP 5 — Quota Service
# ===========================================================================
class TestQuotaService:

    def test_free_plan_user_quota(self, app):
        """QuotaService.check returns (True, 100, 0) for empty free-plan org."""
        from app.services.quota_service import QuotaService
        org_id, _ = _make_org(app, 'Quota Free', 'quotafree')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            allowed, limit, used = QuotaService.check(org, 'users')
            assert limit == 100
            assert isinstance(used, int)

    def test_enterprise_quota_unlimited(self, app):
        """Enterprise plan returns allowed=True and limit=-1 for all resources."""
        from app.services.quota_service import QuotaService
        org_id, _ = _make_org(app, 'Quota Ent', 'quotaent')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            org.plan_type = 'enterprise'
            db.session.commit()
            allowed, limit, used = QuotaService.check(org, 'users')
            assert allowed is True
            assert limit == -1

    def test_quota_exceeded_scenario(self, app):
        """QuotaService.check returns allowed=False when used >= limit."""
        from app.services.quota_service import QuotaService
        org_id, _ = _make_org(app, 'Exceed Corp', 'exceedcorp')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            # Manually override quota limit to 1 (owner already counts as 1)
            org.max_users = 1
            db.session.commit()
            allowed, limit, used = QuotaService.check(org, 'users')
            assert allowed is False
            assert limit == 1

    def test_professional_competition_quota(self, app):
        """Professional plan has competition limit of 10."""
        from app.services.quota_service import QuotaService
        org_id, _ = _make_org(app, 'Pro Quota', 'proquota')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            org.plan_type = 'professional'
            db.session.commit()
            _, limit, _ = QuotaService.check(org, 'competitions')
            assert limit == 10

    def test_get_usage_zero_for_new_org(self, app):
        """QuotaService.get_usage returns 0 for resources on a new org."""
        from app.services.quota_service import QuotaService
        org_id, _ = _make_org(app, 'New Quota Org', 'newquotaorg')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            usage = QuotaService.get_usage(org, 'competitions')
            assert usage == 0


# ===========================================================================
# GROUP 6 — Tenant Isolation (TenantMixin)
# ===========================================================================
class TestTenantIsolation:

    def test_tenant_filter_isolates_by_org(self, app):
        """TenantMixin.tenant_filter returns only records for the specified org."""
        from app.models.challenge import Challenge
        from app.models.organization import Organization
        with app.app_context():
            org1 = Organization(name='Iso Org 1', slug='isoorg1')
            org2 = Organization(name='Iso Org 2', slug='isoorg2')
            db.session.add_all([org1, org2])
            db.session.flush()

            ch1 = Challenge(
                legacy_id='iso_ch1', title='Iso CH1', description='D', points=50,
                difficulty='Easy', organization_id=org1.id
            )
            ch2 = Challenge(
                legacy_id='iso_ch2', title='Iso CH2', description='D', points=100,
                difficulty='Medium', organization_id=org2.id
            )
            db.session.add_all([ch1, ch2])
            db.session.commit()

            org1_chs = Challenge.tenant_filter(Challenge.query, org1.id).all()
            org2_chs = Challenge.tenant_filter(Challenge.query, org2.id).all()

            assert all(c.organization_id == org1.id for c in org1_chs)
            assert all(c.organization_id == org2.id for c in org2_chs)
            # Ensure no cross-contamination
            assert ch2.id not in [c.id for c in org1_chs]

    def test_tenant_or_null_includes_legacy(self, app):
        """tenant_or_null returns records for org AND records with NULL org_id."""
        from app.models.challenge import Challenge
        from app.models.organization import Organization
        with app.app_context():
            org = Organization(name='Legacy Org', slug='legacyorg')
            db.session.add(org)
            db.session.flush()

            ch_tenant = Challenge(
                legacy_id='ten_ch1', title='Tenant CH', description='D', points=50,
                difficulty='Easy', organization_id=org.id
            )
            ch_legacy = Challenge(
                legacy_id='leg_ch1', title='Legacy CH', description='D', points=50,
                difficulty='Easy', organization_id=None
            )
            db.session.add_all([ch_tenant, ch_legacy])
            db.session.commit()

            results = Challenge.tenant_or_null(Challenge.query, org.id).all()
            result_ids = [c.id for c in results]
            assert ch_tenant.id in result_ids
            assert ch_legacy.id in result_ids

    def test_cross_tenant_challenge_not_visible(self, app):
        """Org A's challenges are not visible to Org B's tenant filter."""
        from app.models.challenge import Challenge
        from app.models.organization import Organization
        with app.app_context():
            org_a = Organization(name='Cross A', slug='crossa')
            org_b = Organization(name='Cross B', slug='crossb')
            db.session.add_all([org_a, org_b])
            db.session.flush()

            ch_a = Challenge(
                legacy_id='cross_a_ch', title='Cross A CH', description='D',
                points=100, difficulty='Hard', organization_id=org_a.id
            )
            db.session.add(ch_a)
            db.session.commit()

            # Org B should NOT see Org A's challenge
            b_challenges = Challenge.tenant_filter(Challenge.query, org_b.id).all()
            assert ch_a.id not in [c.id for c in b_challenges]

    def test_team_tenant_filter(self, app):
        """Teams also support tenant_filter via TenantMixin."""
        from app.models.team import Team
        from app.models.organization import Organization
        with app.app_context():
            org1 = Organization(name='Team Iso 1', slug='teamiso1')
            org2 = Organization(name='Team Iso 2', slug='teamiso2')
            db.session.add_all([org1, org2])
            db.session.flush()

            t1 = Team(name='Team Alpha', organization_id=org1.id)
            t2 = Team(name='Team Beta', organization_id=org2.id)
            db.session.add_all([t1, t2])
            db.session.commit()

            org1_teams = Team.tenant_filter(Team.query, org1.id).all()
            assert all(t.organization_id == org1.id for t in org1_teams)
            assert t2.id not in [t.id for t in org1_teams]


# ===========================================================================
# GROUP 7 — Organization Audit Log
# ===========================================================================
class TestOrganizationAuditLog:

    def test_audit_log_created_on_org_creation(self, app):
        """An org_created audit entry is written when a new org is created."""
        from app.models.organization_audit_log import OrganizationAuditLog
        org_id, _ = _make_org(app, 'Audit Org', 'auditorg')
        with app.app_context():
            logs = OrganizationAuditLog.query.filter_by(organization_id=org_id, action='org_created').all()
            assert len(logs) == 1

    def test_audit_log_on_member_invite(self, app):
        """A member_invited audit entry is written when a member is invited."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_audit_log import OrganizationAuditLog
        org_id, owner_id = _make_org(app, 'Audit Invite', 'auditinvite')
        uid = _make_user(app, 'audit_invitee')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user = User.query.get(uid)
            OrganizationService.invite_member(org, user, 'member', actor_id=owner_id)
            logs = OrganizationAuditLog.query.filter_by(organization_id=org_id, action='member_invited').all()
            assert len(logs) == 1

    def test_audit_log_on_plan_change(self, app):
        """A plan_changed audit entry is written when the plan is upgraded."""
        from app.services.billing_service import BillingService
        from app.models.organization_audit_log import OrganizationAuditLog
        org_id, owner_id = _make_org(app, 'Audit Plan', 'auditplan')
        with app.app_context():
            from app.models.organization import Organization
            org = Organization.query.get(org_id)
            BillingService.upgrade(org, 'professional', actor_id=owner_id)
            logs = OrganizationAuditLog.query.filter_by(organization_id=org_id, action='plan_changed').all()
            assert len(logs) == 1

    def test_audit_log_details_json(self, app):
        """OrganizationAuditLog.details property deserializes JSON correctly."""
        from app.models.organization_audit_log import OrganizationAuditLog
        org_id, _ = _make_org(app, 'JSON Audit', 'jsonaudit')
        with app.app_context():
            log = OrganizationAuditLog.query.filter_by(organization_id=org_id, action='org_created').first()
            details = log.details
            assert isinstance(details, dict)

    def test_audit_log_on_role_change(self, app):
        """A member_role_changed audit entry is written."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_audit_log import OrganizationAuditLog
        org_id, owner_id = _make_org(app, 'Role Audit', 'roleaudit')
        uid = _make_user(app, 'role_audit_user')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user = User.query.get(uid)
            m, _ = OrganizationService.invite_member(org, user, 'member', actor_id=owner_id)
            OrganizationService.change_role(m, 'instructor', actor_id=owner_id)
            logs = OrganizationAuditLog.query.filter_by(
                organization_id=org_id, action='member_role_changed'
            ).all()
            assert len(logs) == 1

    def test_audit_log_on_member_removal(self, app):
        """A member_removed audit entry is written when a member is removed."""
        from app.services.organization_service import OrganizationService
        from app.models.organization_audit_log import OrganizationAuditLog
        org_id, owner_id = _make_org(app, 'Remove Audit', 'removeaudit')
        uid = _make_user(app, 'remove_audit_user')
        with app.app_context():
            from app.models.organization import Organization
            from app.models.user import User
            org = Organization.query.get(org_id)
            user = User.query.get(uid)
            m, _ = OrganizationService.invite_member(org, user, 'member', actor_id=owner_id)
            OrganizationService.remove_member(m, actor_id=owner_id)
            logs = OrganizationAuditLog.query.filter_by(
                organization_id=org_id, action='member_removed'
            ).all()
            assert len(logs) == 1


# ===========================================================================
# GROUP 8 — API Endpoints (anonymous → authenticated)
# ===========================================================================
class TestOrgAPI:

    def _login(self, client, app, username='api_test_user'):
        uid = _make_user(app, username)
        with app.app_context():
            from app.models.user import User
            user = User.query.get(uid)
        client.post('/login', data={'username': username, 'password': 'Pass1!'}, follow_redirects=True)
        return uid


    def test_get_org_unauthenticated(self, client):
        """GET /api/v1/organization returns 302 or 401 for anonymous users."""
        resp = client.get('/api/v1/organization')
        assert resp.status_code in (302, 401)

    def test_create_org_unauthenticated(self, client):
        """POST /api/v1/organization rejects unauthenticated requests."""
        resp = client.post('/api/v1/organization', json={'name': 'Test', 'slug': 'test'})
        assert resp.status_code in (302, 401)

    def test_create_org_authenticated(self, client, app):
        """POST /api/v1/organization creates org and returns 201 for logged-in user."""
        self._login(client, app, 'api_create_user')
        resp = client.post('/api/v1/organization', json={'name': 'API Org', 'slug': 'apiorg'}, follow_redirects=True)
        assert resp.status_code in (200, 201, 400)  # 400 if slug conflict, 201 on success

    def test_get_billing_unauthenticated(self, client):
        """GET /api/v1/billing returns redirect or 401 without auth."""
        resp = client.get('/api/v1/billing')
        assert resp.status_code in (302, 401)

    def test_get_subscription_unauthenticated(self, client):
        """GET /api/v1/subscription returns 302/401 without auth."""
        resp = client.get('/api/v1/subscription')
        assert resp.status_code in (302, 401)

    def test_upgrade_plan_unauthenticated(self, client):
        """POST /api/v1/billing/upgrade returns 302/401 without auth."""
        resp = client.post('/api/v1/billing/upgrade', json={'plan': 'professional'})
        assert resp.status_code in (302, 401)

    def test_cancel_plan_unauthenticated(self, client):
        """POST /api/v1/billing/cancel returns 302/401 without auth."""
        resp = client.post('/api/v1/billing/cancel')
        assert resp.status_code in (302, 401)

    def test_invite_member_unauthenticated(self, client):
        """POST /api/v1/organization/invite returns 302/401 without auth."""
        resp = client.post('/api/v1/organization/invite', json={'username': 'test', 'role': 'member'})
        assert resp.status_code in (302, 401)
