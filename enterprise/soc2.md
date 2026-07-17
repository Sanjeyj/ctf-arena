# SOC 2 Trust Services Criteria Mapping
# CTF Arena v1.0.0 — EthicBids Technologies™

This document maps the security, availability, and confidentiality controls of CTF Arena v1.0.0 to the SOC 2 Trust Services Criteria (TSC).

---

## 1. Security Criteria Mapping

* **CC6.1 (Logical Access Controls)**:
  - Enforced via user registration authentication and blueprint RBAC checks.
  - Separate login gateways for participants and administrators.
* **CC6.3 (Transmission Security)**:
  - HTTPS-only cookies (`SESSION_COOKIE_SECURE=True`) and forced TLS v1.2/v1.3 configurations prevent credential interception.
* **CC6.8 (Vulnerability Management)**:
  - Weekly audits via Dependabot and `pip-audit`, with automated hotfix pipelines.

---

## 2. Availability Criteria Mapping

* **A1.1 (Resource Monitoring)**:
  - Prometheus scrapers capture CPU, Memory, Disk Space, and active connections.
* **A1.2 (Backups & Recovery)**:
  - Daily backups via `backup.sh` synced to AWS S3, with verified restore procedures.
* **A1.3 (Capacity Planning)**:
  - Resource scale limits defined for container deployment topologies.
