"""
WarehouseMetric model - Phase 23 Security Data Warehouse.
Stores computed statistics metrics for historical trend analysis.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class WarehouseMetric(db.Model, TimestampMixin, TenantMixin):
    """Data warehouse metric value logs."""
    __tablename__ = 'warehouse_metrics'

    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(120), nullable=False, index=True)
    value = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<WarehouseMetric {self.metric_name} value={self.value}>'

    def to_dict(self):
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
