# Release Candidate Approval Checklist — Cyber Defense Platform

This checklist tracks tasks required to transition the platform from release candidate to production status.

---

## 1. Automated Verification Checks

- [ ] **Linear Database Migrations**: Run `flask db current` to confirm the head matches `8bce79803ffc` with no branch conflicts.
- [ ] **Full Regression Suite**: Run `python -m pytest` and verify that all **1609 / 1609** tests pass successfully.
- [ ] **Smoke Testing**: Execute `smoke_test.py` and `admin_smoke_test.py`. Confirm successful login and participant challenge loads.
- [ ] **DOM Certification**: Run `python scripts/final_dom_certification.py` and verify all **236** checks pass with zero compilation errors.

---

## 2. Security Hardening Checks

- [ ] **Secrets Masking Verification**: Confirm that CTF flags and sensitive api keys are masked in platform executive AI outputs.
- [ ] **Tenant Isolation Verification**: Verify that the database queries isolate data based on `organization_id`.
- [ ] **CSRF Hardening Validation**: Verify that JWT context, Flask-WTF CSRF tokens, and security flags are active across all forms.

---

## 3. Human Approval Sign-off

- [ ] **Acknowledge Production Certification**: Review the final platform cert report.
- [ ] **Populate Release Gate Decisions**: Populate the `ReleaseGateDecision` database record with the authorized administrator's identity.
- [ ] **Set Approval Flag**: Update the approval flag to `True` to enable production server deployment.
