# Operator Maintenance Checklist — Cyber Defense Platform

This checklist is used by platform operators to perform regular system health checks.

---

## 1. Daily Health Audits

- [ ] **Review Golden Signals**: Access `/admin/operations-fabric/health` and verify all services report `HEALTHY`.
- [ ] **Monitor Active Incidents**: Access `/admin/operations-fabric/incidents`. Ensure there are no unresolved critical operational incidents.
- [ ] **Check Ingestion Health**: Verify telemetry metrics update inside `/admin/operations-fabric/telemetry`.
- [ ] **Verify SQLite DB Locks**: Inspect application logs for database connection locks or long-running SQLite write operations.

---

## 2. Weekly Health Audits

- [ ] **Run Scheduled Backups**: Take a daily cold database backup and verify backup integrity via `sqlite3 backups/backup.db "PRAGMA integrity_check;"`.
- [ ] **Inspect API Latencies**: Access the distributed tracing log at `/admin/operations-fabric/traces` and confirm that average route latencies remain under 10ms.
- [ ] **Audit Compliance Frameworks**: Check overall GRC compliance stats at `/admin/compliance`. Confirm that NIST/ISO security gates remain at 100%.

---

## 3. Incident Escalation Workflow

1. **Verify Alert**: Verify the alert in the Operational Incidents queue.
2. **Review Traces**: Use `/admin/operations-fabric/traces` to identify database queries or API routes that exceed 1000ms duration.
3. **Trigger Playbooks**: Follow the playbooks index on the Validation dashboard.
4. **Deploy Hotfix**: Ensure that changes are run through the test regression suite before application restart.
