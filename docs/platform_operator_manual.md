# Platform Operator Manual

## 1. System Ingestion Monitoring

Platform operators manage system telemetry, service health queues, and distributed trace spans.

---

## 2. Monitoring Golden Signals

- Golden signals availability and latency logs are viewed via the `/admin/operations-fabric/health` dashboard.
- **Latency Alerts**: Spans executing for longer than 500ms display warning states. Any query or API latency exceeding 1000ms triggers a critical status tag.
- **Saturation Thresholds**: Memory, queue, and database saturation indicators trigger warnings at 80% usage and critical statuses at 95% usage.

---

## 3. Incident Correlation & Escalation

- Active alerts and system exceptions are aggregated under `/admin/operations-fabric/incidents`.
- Operators audit root causes and log mitigations.
- Use the validation dashboard to verify playbook readiness after resolving an incident.
