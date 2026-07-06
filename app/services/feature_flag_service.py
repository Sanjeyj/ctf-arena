"""
FeatureFlagService - Phase 31 Cyber Platform Control Plane.
Tenant-aware feature flags management.
Evaluation uses a stable cryptographic SHA-256 hash to ensure deterministic rollout.
"""
from app.extensions import db
from app.models.platform_feature_flag import PlatformFeatureFlag
import hashlib
import json


class FeatureFlagService:
    @staticmethod
    def create_flag(flag_key: str, org_id: int, description: str = None, enabled: bool = False, rollout_percentage: int = 100, conditions: dict = None) -> PlatformFeatureFlag:
        """Create a platform feature flag."""
        cond_str = json.dumps(conditions) if conditions else None
        flag = PlatformFeatureFlag(
            flag_key=flag_key,
            description=description,
            enabled=enabled,
            rollout_percentage=max(0, min(100, rollout_percentage)),
            environment='production',
            conditions_json=cond_str,
            organization_id=org_id
        )
        db.session.add(flag)
        db.session.commit()
        return flag

    @staticmethod
    def enable(flag_id: int, org_id: int) -> PlatformFeatureFlag:
        """Enable flag key."""
        flag = db.session.get(PlatformFeatureFlag, flag_id)
        if not flag or flag.organization_id != org_id:
            return None
        flag.enabled = True
        db.session.commit()
        return flag

    @staticmethod
    def disable(flag_id: int, org_id: int) -> PlatformFeatureFlag:
        """Disable flag key."""
        flag = db.session.get(PlatformFeatureFlag, flag_id)
        if not flag or flag.organization_id != org_id:
            return None
        flag.enabled = False
        db.session.commit()
        return flag

    @staticmethod
    def evaluate(flag_key: str, user_id: str, org_id: int) -> bool:
        """Evaluate feature flag status deterministically using SHA-256 hashes."""
        flag = PlatformFeatureFlag.query.filter_by(flag_key=flag_key, organization_id=org_id).first()
        if not flag:
            return False
        if not flag.enabled:
            return False
        if flag.rollout_percentage == 100:
            return True
        if flag.rollout_percentage == 0:
            return False

        # Stable cryptographic hash check
        hash_input = f"{org_id}:{user_id}:{flag_key}".encode()
        hval = int(hashlib.sha256(hash_input).hexdigest(), 16) % 100
        return hval < flag.rollout_percentage

    @staticmethod
    def rollout_status(flag_id: int, org_id: int) -> dict:
        """Retrieve flag status parameters."""
        flag = db.session.get(PlatformFeatureFlag, flag_id)
        if not flag or flag.organization_id != org_id:
            return {}
        return {
            'flag_key': flag.flag_key,
            'enabled': flag.enabled,
            'rollout_percentage': flag.rollout_percentage,
        }
