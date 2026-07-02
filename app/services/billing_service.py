from app.extensions import db
from app.models.organization_billing import OrganizationBilling
from app.models.organization_audit_log import OrganizationAuditLog
from app.models.organization import Organization
import datetime

class BillingService:
    @staticmethod
    def get_billing(org: Organization) -> OrganizationBilling:
        billing = OrganizationBilling.query.filter_by(organization_id=org.id).first()
        if not billing:
            billing = OrganizationBilling(
                organization_id=org.id,
                plan_type=org.plan_type,
                status='trial',
                trial_ends_at=datetime.datetime.utcnow() + datetime.timedelta(days=14)
            )
            db.session.add(billing)
            db.session.commit()
        return billing

    @staticmethod
    def upgrade(org: Organization, plan: str, actor_id: int = None) -> tuple[bool, str]:
        """Upgrade or switch the subscription plan for an organization."""
        if plan not in ('free', 'professional', 'enterprise'):
            return False, "Invalid plan type."

        billing = BillingService.get_billing(org)
        old_plan = org.plan_type
        
        # State machine transition
        success, err = billing.transition_to('active')
        if not success:
            # If currently trial, we can transition to active
            # If already active, switching plans is fine but the status remains active.
            if billing.status == 'active':
                pass
            else:
                return False, err

        org.plan_type = plan
        billing.plan_type = plan
        billing.current_period_start = datetime.datetime.utcnow()
        billing.current_period_end = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        
        # Log audit
        audit = OrganizationAuditLog(
            organization_id=org.id,
            user_id=actor_id,
            action='plan_changed',
            resource_type='organization',
            resource_id=org.id
        )
        audit.details = {'old_plan': old_plan, 'new_plan': plan, 'status': billing.status}
        db.session.add(audit)
        
        db.session.commit()
        return True, "Plan updated successfully."

    @staticmethod
    def cancel(org: Organization, actor_id: int = None) -> tuple[bool, str]:
        """Cancel subscription immediately, transitioning to cancelled status."""
        billing = BillingService.get_billing(org)
        success, err = billing.transition_to('cancelled')
        if not success:
            return False, err

        # Downgrade plan type to free upon cancellation
        old_plan = org.plan_type
        org.plan_type = 'free'
        billing.plan_type = 'free'
        
        audit = OrganizationAuditLog(
            organization_id=org.id,
            user_id=actor_id,
            action='billing_status_changed',
            resource_type='organization',
            resource_id=org.id
        )
        audit.details = {'old_plan': old_plan, 'new_plan': 'free', 'old_status': 'active', 'new_status': 'cancelled'}
        db.session.add(audit)
        
        db.session.commit()
        return True, "Subscription cancelled successfully."

    @staticmethod
    def mark_past_due(org: Organization, actor_id: int = None) -> tuple[bool, str]:
        """Transition subscription status to past_due."""
        billing = BillingService.get_billing(org)
        success, err = billing.transition_to('past_due')
        if not success:
            return False, err

        audit = OrganizationAuditLog(
            organization_id=org.id,
            user_id=actor_id,
            action='billing_status_changed',
            resource_type='organization',
            resource_id=org.id
        )
        audit.details = {'status': 'past_due'}
        db.session.add(audit)
        
        db.session.commit()
        return True, "Subscription marked as past due."

    @staticmethod
    def is_active(org: Organization) -> bool:
        billing = BillingService.get_billing(org)
        return billing.is_active()
