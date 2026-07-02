# Changelog — CTF Arena

All notable changes to the CTF Arena project will be documented in this file.

---

## [1.0.0-rc1] — 2026-07-02

### Added
- **Architectural Migration**: Modular design factory pattern with 15+ sub-blueprints replacing the legacy single-file script.
- **Docker-based Challenges**: Built-in container life cycle management (spawning, dynamic mapping, and background daemon pruning).
- **PostgreSQL Compatibility**: Migrated and verified SQL mappings for Postgres database installations.
- **Observability and Monitoring**: Added Prometheus-compatible `/metrics` and detailed `/health` endpoints.
- **RBAC Infrastructure**: Multi-role support (Admin, Moderator, Challenge Author, Participant, Guest).
- **Security Hardening**:
  - CSRF validation active on all HTTP forms.
  - Safe download headers (`Content-Disposition: attachment` & `X-Content-Type-Options: nosniff`).
  - Account lockouts after 5 consecutive failed logins.
  - Strict Content Security Policy (CSP).
- **Performance Optimizations**: Eager load joins (`joinedload`) to prevent N+1 query patterns.

### Fixed
- **Rollback Failures**: All repository writes migrated to `safe_commit()` wrapping transactions in robust database rollbacks.
- **Timezone Modernization**: Replaced deprecated `datetime.utcnow()` calls with clean, naive UTC timestamps to avoid calculations drift.
