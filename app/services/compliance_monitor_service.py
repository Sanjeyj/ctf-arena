"""
ComplianceMonitorService - Phase 26 Autonomous Cyber Enterprise.
Monitors alignment with governance frameworks and detects real-time drift.
"""
from app.extensions import db, utcnow
from app.models.compliance_monitor import ComplianceMonitor

class ComplianceMonitorService:
    @staticmethod
    def evaluate_framework(framework: str, organization_id: int) -> ComplianceMonitor:
        """Create or locate a framework compliance monitor instance."""
        monitor = ComplianceMonitor.query.filter_by(
            framework=framework,
            organization_id=organization_id
        ).first()

        if not monitor:
            monitor = ComplianceMonitor(
                framework=framework,
                score=100.0,
                drift_status='stable',
                last_check=utcnow(),
                organization_id=organization_id
            )
            db.session.add(monitor)
            db.session.commit()
        return monitor

    @staticmethod
    def detect_drift(framework: str, organization_id: int) -> dict:
        """Simulate real-time checking of compliance drift based on active controls."""
        monitor = ComplianceMonitorService.evaluate_framework(framework, organization_id)
        
        # Simulating drift analysis: if score drops below 90, drift is detected.
        if monitor.score < 90.0:
            monitor.drift_status = 'drift_detected'
        else:
            monitor.drift_status = 'stable'
            
        monitor.last_check = utcnow()
        db.session.commit()

        return {
            'framework': monitor.framework,
            'current_score': monitor.score,
            'drift_status': monitor.drift_status,
            'last_check': monitor.last_check.isoformat()
        }

    @staticmethod
    def calculate_score(framework: str, organization_id: int) -> float:
        """Calculate and update the compliance score."""
        monitor = ComplianceMonitorService.evaluate_framework(framework, organization_id)
        
        # Calculate score (in mock setup, we return the saved score or adjust it slightly)
        # Let's say if drift is detected, we penalty by 15 points, otherwise keep it at 95.0
        if monitor.drift_status == 'drift_detected':
            monitor.score = 80.0
        else:
            monitor.score = 95.0
            
        db.session.commit()
        return monitor.score
