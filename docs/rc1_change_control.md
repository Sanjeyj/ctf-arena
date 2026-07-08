# Release Candidate Change Control (v1.0.0)

**Date**: 2026-07-08  
**Release Candidate Reference**: `v1.0.0-rc1` (commit `cca83fa`)  
**Proposed Final Release Commit**: `072efa2`

---

## Post-RC Changes List

The following changes were introduced after the `v1.0.0-rc1` tag:

### Change 1 — Phase 34-40 Wiring and Hook Registrations

- **Commit**: `072efa2`
- **Changed Files**:
  - `app/__init__.py` — Registered blueprints and CSRF exemptions for Phase 34–40 fabrics.
  - `app/models/__init__.py` — Registered Phase 34–40 models.
  - `app/services/hook_service.py` — Registered hook definitions for Phase 34–39 hooks.
- **Classification**: **Compatibility / Integration Fix**
- **Reason**: These imports and configurations were untracked in the working tree during the RC tagging process. They represent the completion of platform wiring across all implemented phases.
- **Risk**: ⚪ **Low** — no changes to database tables or operational logic. Simply exposes blueprints and registers them with the Flask container.
- **Tests Executed**: Full 1609 regression suite.
- **Approval Requirement**: Approved by release engineer.

---

### Change 2 — Finding Service Hook Iteration Fix

- **Commit**: `072efa2`
- **Changed Files**:
  - `app/services/finding_service.py` — Fixed the hook response iteration logic.
- **Classification**: **Defect Fix**
- **Reason**: The hook invocation in `FindingService` returns a list of dictionaries rather than a single dictionary. Iterating over the list prevents a `KeyError` or unexpected behavior when multiple hooks are registered.
- **Risk**: ⚪ **Low** — defensive programming improvement.
- **Tests Executed**: `tests/test_exposure_findings.py` (all tests passed).
- **Approval Requirement**: Approved by release engineer.

---

## Schema Changes

- **Schema Changes**: `0`
- No migrations were created or modified during the stabilization phase. The migration head remains exactly `8bce79803ffc`.

---

## Change Risk Summary

All post-RC changes are classified as low-risk integration alignment and minor bug-fixing. No new features or tables were added. The full 1609-test regression suite passes successfully on the post-RC commit `072efa2`.
