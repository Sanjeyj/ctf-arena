"""
OperationsService - Phase 29 Global Cyber Command Center.
Manages global cyber operations lifecycle: create, assign, close.
"""
import datetime
from app.extensions import db
from app.models.global_operation import GlobalOperation


class OperationsService:
    @staticmethod
    def create_operation(name: str, operation_type: str, severity: str, org_id: int) -> GlobalOperation:
        """Create a new global cyber operation."""
        op = GlobalOperation(
            name=name,
            operation_type=operation_type,
            severity=severity,
            status='planned',
            start_time=datetime.datetime.utcnow(),
            organization_id=org_id,
        )
        db.session.add(op)
        db.session.commit()
        return op

    @staticmethod
    def assign(operation_id: int) -> GlobalOperation:
        """Assign an operation, moving it from planned to active."""
        op = db.session.get(GlobalOperation, operation_id)
        if not op:
            return None
        op.status = 'active'
        db.session.commit()
        return op

    @staticmethod
    def close(operation_id: int) -> GlobalOperation:
        """Close a completed or aborted operation."""
        op = db.session.get(GlobalOperation, operation_id)
        if not op:
            return None
        op.status = 'complete'
        op.end_time = datetime.datetime.utcnow()
        db.session.commit()
        return op
