# Test Failure Triage Runbook

**Purpose**: Steps to investigate and resolve test failures in the CDP test suite.  
**Expected Baseline**: 1609 tests passing, 0 failing.

---

## Prerequisites

- Virtual environment activated
- Test database (`sqlite:///:memory:`) isolated per test
- `pytest` installed

---

## Triage Procedure

### Step 1 — Identify Failing Tests

```bash
# Run full suite and capture failures
python -m pytest --tb=short -q 2>&1 | Tee-Object test_output.txt

# List only failing tests
python -m pytest --tb=line -q 2>&1 | Select-String "FAILED"
```

### Step 2 — Run a Single Failing Test

```bash
python -m pytest tests/test_<module>.py::test_<function_name> -v --tb=long
```

### Step 3 — Check for Import Errors

```bash
python -m pytest tests/test_<module>.py --collect-only
```

If collection fails, the test module has an import error. Check:
- Missing models in `app/models/__init__.py`
- Missing services in `app/services/`
- Missing blueprint registration in `app/__init__.py`

### Step 4 — Isolate Environment Issues

```bash
# Verify migration head is correct
flask db current

# Verify all dependencies are installed
pip check
```

### Step 5 — Check for Database State Leakage

If a test fails only when run with the full suite but passes in isolation:
- The test fixture is not properly isolating state.
- Check that `db.session.rollback()` or `db.drop_all()` is called in test teardown.

---

## Common Failure Patterns

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `ImportError: cannot import name X` | Missing `__init__.py` export | Add model/service to `__init__.py` |
| `OperationalError: no such table` | Migration not applied | Run `flask db upgrade` |
| `AssertionError: 404 != 200` | Blueprint not registered | Check `register_blueprints()` in `app/__init__.py` |
| `IntegrityError: UNIQUE constraint` | Test state leakage | Check fixture teardown |
| `KeyError` in service | Hook result type mismatch | Verify hook returns a list of dicts |

---

## Governance Rule

> **DO NOT weaken tests to make failures pass.** If a test reveals a genuine bug, fix the application code, not the test assertion.

---

## Escalation Condition

Escalate to senior engineer if:
- More than 10 tests fail in the same module
- Failures are non-deterministic (flaky tests)
- A migration change causes cascading test failures across multiple modules

---

## Audit Evidence to Retain

- Full `pytest` output with timestamps
- Names of all failing tests
- Root cause diagnosis notes
- Commit reference for any fix applied
