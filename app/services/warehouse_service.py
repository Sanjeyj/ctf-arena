"""
Warehouse Service - Phase 23 Security Data Warehouse.
Performs historical trend analysis, metric storage, and raw events aggregation.
"""
import datetime
from app.extensions import db
from app.models.warehouse_event import WarehouseEvent
from app.models.warehouse_metric import WarehouseMetric

class WarehouseService:

    @staticmethod
    def aggregate_events(source: str, org_id: int = None) -> list[WarehouseEvent]:
        q = WarehouseEvent.query.filter_by(source=source)
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()

    @staticmethod
    def store_metric(name: str, value: float, org_id: int = None) -> WarehouseMetric:
        metric = WarehouseMetric(
            metric_name=name,
            value=value,
            timestamp=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @staticmethod
    def analyze_trends(metric_name: str, org_id: int = None) -> list[WarehouseMetric]:
        q = WarehouseMetric.query.filter_by(metric_name=metric_name).order_by(WarehouseMetric.timestamp.desc())
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()
