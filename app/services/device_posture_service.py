"""
DevicePostureService - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores simulated device security posture and evaluates compliance status.
"""
from app.extensions import db
from app.models.device_posture import DevicePosture
import datetime


class DevicePostureService:
    @staticmethod
    def register_device(device_name: str, device_type: str, os_family: str, org_id: int, patch_score: float = 1.0, encryption_enabled: bool = True, endpoint_protection_status: str = 'active') -> DevicePosture:
        """Register simulated device security posture."""
        device = DevicePosture(
            device_name=device_name,
            device_type=device_type,
            os_family=os_family,
            patch_score=max(0.0, min(1.0, patch_score)),
            encryption_enabled=encryption_enabled,
            endpoint_protection_status=endpoint_protection_status,
            compliance_status='compliant',
            organization_id=org_id
        )
        DevicePostureService.calculate_posture(device)
        db.session.add(device)
        db.session.commit()
        return device

    @staticmethod
    def calculate_posture(device: DevicePosture) -> float:
        """Calculate posture score, clamping output to [0.0, 100.0]."""
        # base: patch_score * 50 + (50 if encryption_enabled else 0)
        # deduct 30 if endpoint protection is inactive, and 50 if not_installed
        base = (device.patch_score * 50.0) + (50.0 if device.encryption_enabled else 0.0)
        if device.endpoint_protection_status == 'inactive':
            base -= 30.0
        elif device.endpoint_protection_status == 'not_installed':
            base -= 50.0
        
        score = max(0.0, min(100.0, base))
        device.posture_score = round(score, 2)
        
        # update compliance classification
        if score >= 70.0 and device.encryption_enabled:
            device.compliance_status = 'compliant'
        elif score >= 40.0:
            device.compliance_status = 'restricted'
        else:
            device.compliance_status = 'non_compliant'

        return device.posture_score

    @staticmethod
    def assess(device_id: int, org_id: int) -> DevicePosture:
        """Assess device compliance status and update posture scores."""
        device = db.session.get(DevicePosture, device_id)
        if not device or device.organization_id != org_id:
            return None
        device.last_assessed_at = datetime.datetime.utcnow()
        DevicePostureService.calculate_posture(device)
        db.session.commit()
        return device

    @staticmethod
    def explain_posture(device_id: int, org_id: int) -> str:
        """Provide detailed human-readable explanation of device posture assessment."""
        device = db.session.get(DevicePosture, device_id)
        if not device or device.organization_id != org_id:
            return "Device not found."

        reasons = []
        if not device.encryption_enabled:
            reasons.append("Device storage encryption is disabled.")
        if device.endpoint_protection_status != 'active':
            reasons.append("Endpoint protection is not active or missing.")
        if device.patch_score < 0.8:
            reasons.append("Operating system patches are severely outdated.")
        
        if not reasons:
            reasons.append("All endpoint protection controls are verified and compliant.")

        return f"Device posture score is {device.posture_score}/100 ({device.compliance_status}). Checks: " + " ".join(reasons)
