# Operations Handover Document
# CTF Arena v1.0.0 — EthicBids Technologies™

This document delivers the complete operations handover package to the production operations team.

---

## 1. Runbook Index

The following operational runbooks are available for the production platform:

| Runbook | Location | Covers |
|---------|----------|--------|
| **Disaster Recovery** | `docs/disaster_recovery_ops.md` | Database restore, full server recovery, disk exhaustion |
| **Backup & Restore** | `scripts/backup.sh`, `scripts/restore.sh` | Automated backups, archive restore procedures |
| **Production Validation** | `docs/production_validation.md` | Post-deployment validation and functional walkthrough |
| **Incident Response** | `release/INCIDENT_RESPONSE_GUIDE.md` | Security incidents, brute-force, flag leaks, host compromise |
| **Rollback** | `release/ROLLBACK_CHECKLIST.md` | Container image revert, database state reset |

---

## 2. Incident Response Summary

| Severity | Definition | Escalation Path | SLA |
|----------|-----------|-----------------|-----|
| **Sev 1 — Critical** | Total platform outage or security breach | On-call engineer → Security Lead → CTO | **< 1 hour** |
| **Sev 2 — Major** | Key feature failure (e.g. auth down) | On-call engineer → Team Lead | **< 4 hours** |
| **Sev 3 — Minor** | Localised errors or UI regressions | Next business day | **< 24 hours** |

---

## 3. Monitoring Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **Grafana Overview** | `https://arena.ethicbids.app:3000` | Real-time metrics, CPU, memory, request rates |
| **Prometheus Targets** | `http://prometheus:9090/targets` (internal) | Scrape target health per job |

---

## 4. Maintenance Schedule Summary

| Frequency | Task | Responsibility |
|-----------|------|---------------|
| **Daily** | Review backup log file at `/opt/ctf-arena/logs/backup.log` | Ops Engineer |
| **Weekly** | Check Prometheus alert rules and disk usage | Ops Engineer |
| **Monthly** | OS security patches, staging restore drill | SysAdmin |
| **Quarterly** | Dependency audit (`pip-audit`) and patch release | Core Dev Team |

---

## 5. Escalation Matrix

| Contact Role | Name | Contact |
|---|---|---|
| **On-Call Engineer** | Ops Team Primary | ops-oncall@ethicbids.app |
| **Security Lead** | Security Team | security@ethicbids.app |
| **System Architect** | Platform Lead | architect@ethicbids.app |
| **Business Owner** | EthicBids Management | management@ethicbids.app |
