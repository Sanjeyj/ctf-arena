"""
TelemetryService - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Handles simulated metric ingestion and querying.
"""
from app.extensions import db
from app.models.telemetry_source import TelemetrySource
from app.models.telemetry_metric import TelemetryMetric
from app.services.hook_service import HookService
import datetime
import json


class TelemetryService:
    @staticmethod
    def register_source(name: str, source_type: str, module_name: str, org_id: int, collection_interval: int = 60) -> TelemetrySource:
        """Register a telemetry source."""
        src = TelemetrySource(
            name=name,
            source_type=source_type,
            module_name=module_name,
            collection_interval=collection_interval,
            status='active',
            health_score=1.0,
            last_collection_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(src)
        db.session.commit()
        return src

    @staticmethod
    def ingest_metric(source_id: int, metric_name: str, metric_type: str, metric_value: float, org_id: int, unit: str = None, dimensions_json: dict = None) -> TelemetryMetric:
        """Ingest a telemetry metric, triggering hooks and normalizing metric values."""
        # Controlled mutation via before_telemetry_ingest hook
        hook_results = HookService.trigger_hook(
            'before_telemetry_ingest',
            source_id=source_id,
            metric_name=metric_name,
            metric_type=metric_type,
            metric_value=metric_value,
            unit=unit,
            dimensions_json=dimensions_json,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                if 'metric_value' in res:
                    metric_value = res['metric_value']
                if 'dimensions_json' in res:
                    dimensions_json = res['dimensions_json']
                if 'unit' in res:
                    unit = res['unit']

        src = db.session.get(TelemetrySource, source_id)
        if not src or src.organization_id != org_id:
            return None

        # Update last collection time
        src.last_collection_at = datetime.datetime.utcnow()
        # Source health recalculation in case it was degraded
        src.status = 'active'
        src.health_score = 1.0

        normalized_value = TelemetryService.normalize_metric(metric_value, unit)

        metric = TelemetryMetric(
            source_id=source_id,
            metric_name=metric_name,
            metric_type=metric_type,
            metric_value=normalized_value,
            unit=unit,
            dimensions_json=json.dumps(dimensions_json) if dimensions_json else None,
            recorded_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(metric)
        db.session.commit()

        HookService.trigger_hook('after_telemetry_ingest', metric=metric)

        return metric

    @staticmethod
    def normalize_metric(metric_value: float, unit: str = None) -> float:
        """Normalize metric value deterministically."""
        # If the unit is a percentage (e.g. '%' or 'percentage') and metric_value > 1.0, scale it to 0.0 - 1.0
        if unit in ['%', 'percentage']:
            if metric_value > 1.0:
                return round(metric_value / 100.0, 4)
        return float(metric_value)

    @staticmethod
    def query_metrics(source_id: int, metric_name: str, start_time: datetime.datetime, end_time: datetime.datetime, org_id: int) -> list:
        """Query metrics by source within a time window."""
        return TelemetryMetric.query.filter(
            TelemetryMetric.source_id == source_id,
            TelemetryMetric.metric_name == metric_name,
            TelemetryMetric.recorded_at >= start_time,
            TelemetryMetric.recorded_at <= end_time,
            TelemetryMetric.organization_id == org_id
        ).all()

    @staticmethod
    def source_health(source_id: int, org_id: int) -> TelemetrySource:
        """Recalculate telemetry source health based on heartbeat window."""
        src = db.session.get(TelemetrySource, source_id)
        if not src or src.organization_id != org_id:
            return None

        if src.last_collection_at:
            delta = (datetime.datetime.utcnow() - src.last_collection_at).total_seconds()
            # If we missed collection interval by more than double, mark degraded
            if delta > (src.collection_interval * 2):
                src.status = 'degraded'
                src.health_score = 0.5
            else:
                src.status = 'active'
                src.health_score = 1.0
        else:
            src.status = 'inactive'
            src.health_score = 0.0

        db.session.commit()
        return src

    @staticmethod
    def telemetry_summary(org_id: int) -> dict:
        """Provide overview numbers for telemetry fabric."""
        sources = TelemetrySource.query.filter_by(organization_id=org_id).all()
        metric_count = TelemetryMetric.query.filter_by(organization_id=org_id).count()
        if not sources:
            return {
                'total_sources': 0,
                'active_sources': 0,
                'degraded_sources': 0,
                'inactive_sources': 0,
                'avg_health': 1.0,
                'total_metrics': metric_count
            }

        active = sum(1 for s in sources if s.status == 'active')
        degraded = sum(1 for s in sources if s.status == 'degraded')
        inactive = sum(1 for s in sources if s.status == 'inactive')
        avg_health = sum(s.health_score for s in sources) / len(sources)

        return {
            'total_sources': len(sources),
            'active_sources': active,
            'degraded_sources': degraded,
            'inactive_sources': inactive,
            'avg_health': round(avg_health, 3),
            'total_metrics': metric_count
        }
