# CIS Critical Security Controls Mapping
# CTF Arena v1.0.0 — EthicBids Technologies™

This document maps platform security practices to the CIS Critical Security Controls (v8).

---

## 1. CIS Controls Alignment

### CIS Control 3: Data Protection
- Active encryption in transit (TLS 1.2+ forced).
- Symmetric GPG encryption on backups.
- Sensitive environment variables stored out of git source tree.

### CIS Control 4: Secure Configuration of Enterprise Assets
- Production containers run on a stripped down Debian base (`python:3.11-slim`).
- Application process executes under non-root UID 1001 with read-only storage mounting.

### CIS Control 5: Account Management
- Seeded admin password must be customized on start.
- Explicit RBAC controls prevent regular participants from executing operations panel tasks.

### CIS Control 11: Data Recovery
- Scheduled daily backups of user data and configuration files with tested restore runbooks.
