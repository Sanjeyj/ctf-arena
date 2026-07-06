"""
TraceService - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Simulates trace logging, spans construction, critical path calculation, and tree visualizer helper.
"""
from app.extensions import db
from app.models.trace_record import TraceRecord
import datetime
import json


class TraceService:
    @staticmethod
    def start_trace(trace_id: str, span_id: str, service_name: str, operation_name: str, org_id: int) -> TraceRecord:
        """Initialize a new trace root span."""
        record = TraceRecord(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            service_name=service_name,
            operation_name=operation_name,
            duration_ms=0.0,
            status='success',
            started_at=datetime.datetime.utcnow(),
            completed_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def add_span(trace_id: str, span_id: str, parent_span_id: str, service_name: str, operation_name: str, org_id: int) -> TraceRecord:
        """Add a child span to a trace."""
        record = TraceRecord(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            service_name=service_name,
            operation_name=operation_name,
            duration_ms=0.0,
            status='success',
            started_at=datetime.datetime.utcnow(),
            completed_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def complete_span(span_id: str, duration_ms: float, status: str, org_id: int, metadata_json: dict = None) -> TraceRecord:
        """Complete an existing span, updating status and duration."""
        # Find span (there can be multiple traces, but span_id is usually unique or scoped to tenant)
        record = TraceRecord.query.filter_by(span_id=span_id, organization_id=org_id).first()
        if not record:
            return None
        record.duration_ms = max(0.0, float(duration_ms))
        record.status = status
        record.completed_at = record.started_at + datetime.timedelta(milliseconds=duration_ms)
        if metadata_json:
            record.metadata_json = json.dumps(metadata_json)
        db.session.commit()
        return record

    @staticmethod
    def build_trace_tree(trace_id: str, org_id: int) -> dict:
        """Build hierarchical span tree, ensuring cycle protection."""
        spans = TraceRecord.query.filter_by(trace_id=trace_id, organization_id=org_id).all()
        if not spans:
            return {}

        # Build map
        span_map = {s.span_id: s.to_dict() for s in spans}
        roots = []
        children = {s.span_id: [] for s in spans}

        # Associate parent/child relationships
        for s in spans:
            pid = s.parent_span_id
            if pid and pid in span_map:
                children[pid].append(s.span_id)
            else:
                roots.append(s.span_id)

        # Recursively construct tree with cycle detection
        visited = set()

        def build_node(sid):
            if sid in visited:
                # Cycle detected, return node with error indicator
                node = dict(span_map[sid])
                node['children'] = []
                node['cycle_detected'] = True
                return node

            visited.add(sid)
            node = dict(span_map[sid])
            node['children'] = [build_node(cid) for cid in children[sid]]
            visited.remove(sid)
            return node

        tree_nodes = [build_node(rid) for rid in roots]
        return {
            'trace_id': trace_id,
            'roots': tree_nodes
        }

    @staticmethod
    def calculate_critical_path(trace_id: str, org_id: int) -> list:
        """Calculate critical path (longest execution sequence of dependent spans)."""
        spans = TraceRecord.query.filter_by(trace_id=trace_id, organization_id=org_id).all()
        if not spans:
            return []

        # Map span_id to object
        span_map = {s.span_id: s for s in spans}
        # Parent to children map
        children = {s.span_id: [] for s in spans}
        roots = []

        for s in spans:
            pid = s.parent_span_id
            if pid and pid in span_map:
                children[pid].append(s.span_id)
            else:
                roots.append(s.span_id)

        # Depth-First Search to find longest path weight
        memo = {}
        visited = set()

        def get_max_path(sid):
            if sid in visited:
                return 0.0, []  # Cycle protection
            if sid in memo:
                return memo[sid]

            visited.add(sid)
            span_duration = span_map[sid].duration_ms
            max_child_weight = 0.0
            max_child_path = []

            for cid in children[sid]:
                weight, path = get_max_path(cid)
                if weight > max_child_weight:
                    max_child_weight = weight
                    max_child_path = path

            memo[sid] = (span_duration + max_child_weight, [sid] + max_child_path)
            visited.remove(sid)
            return memo[sid]

        global_max_weight = -1.0
        critical_path = []

        for rid in roots:
            weight, path = get_max_path(rid)
            if weight > global_max_weight:
                global_max_weight = weight
                critical_path = path

        return [span_map[sid].to_dict() for sid in critical_path]

    @staticmethod
    def trace_summary(org_id: int) -> dict:
        """Report overview trace metrics."""
        spans = TraceRecord.query.filter_by(organization_id=org_id).all()
        if not spans:
            return {
                'total_spans': 0,
                'total_traces': 0,
                'avg_duration_ms': 0.0,
                'error_rate': 0.0
            }

        trace_ids = {s.trace_id for s in spans}
        total_spans = len(spans)
        avg_duration = sum(s.duration_ms for s in spans) / total_spans
        error_spans = sum(1 for s in spans if s.status == 'error')
        error_rate = error_spans / total_spans

        return {
            'total_spans': total_spans,
            'total_traces': len(trace_ids),
            'avg_duration_ms': round(avg_duration, 2),
            'error_rate': round(error_rate, 4)
        }
