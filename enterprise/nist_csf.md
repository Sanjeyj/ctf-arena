# NIST CSF Compliance Mapping
# CTF Arena v1.0.0 — EthicBids Technologies™

This document maps CTF Arena v1.0.0 features and tools to the NIST Cybersecurity Framework (CSF) Core Functions.

---

## 1. Core Function Mapping

### Identify (ID)
* **ID.AM (Asset Management)**: Supported via docker-compose configuration files and SBOM manifests generated at build time.
* **ID.RA (Risk Assessment)**: Custom risk scoring and Monte Carlo analysis are integrated into the GRC platform modules.

### Protect (PR)
* **PR.AC (Identity Management & Access Control)**: Enforced via password hashing, CSRF verification, session timeouts, and role mapping.
* **PR.DS (Data Security)**: Cryptographic protection for data in transit (HTTPS) and at rest (encrypted database backups).

### Detect (DE)
* **DE.CM (Security Continuous Monitoring)**: Exposing system metrics via `/metrics` and security logs via Gunicorn error outputs.

### Respond & Recover (RS / RC)
* **RS.RP / RC.RP (Recovery Planning)**: Supported by the automated backup scripts, staging restore validations, and disaster recovery playbooks.
