# Platform Release & Deployment Manual

## 1. Upgrades

Upgrades must follow verification and linear migration checks:

```
[Create Database Backup] ──> [Apply Migrations] ──> [Run Verification Test Suite] ──> [Launch Web Service]
```

### Pre-Deployment Verification Checklist
1. Validate database file state.
2. Confirm the Alembic migration head matches `8bce79803ffc`.
3. Execute the full test suite (`python -m pytest`). All tests must pass before launching the web service.

---

## 2. Gate Evaluation

- Before production deployment, the platform evaluates 6 automated release gates:
  - Unit Tests
  - Security Hardening
  - Tenant Isolation
  - AI Safety
  - Migration Linearity
  - Documentation Coverage
- Human sign-off is required to approve the release gate decisions.
