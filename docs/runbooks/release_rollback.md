# Release Rollback Runbook

**Purpose**: Procedure for rolling back from `v1.0.0` to `v1.0.0-rc1` if a critical defect is discovered post-release.

---

## Prerequisites

- Access to the git repository
- Database backup from before `v1.0.0` deployment
- Confirmation from release authority that rollback is authorized

---

## Rollback Procedure

### Step 1 — Stop the Application

Follow the [shutdown runbook](./shutdown.md).

### Step 2 — Checkout Previous Release

```bash
git checkout v1.0.0-rc1
```

Or to a specific commit:

```bash
git checkout cca83fa
```

### Step 3 — Restore Database Backup

> ⚠ **Only if schema changes were made in v1.0.0 that need to be reversed.**

```bash
# Stop all connections first
# Restore from pre-v1.0.0 backup
Copy-Item instance/ctf_pre_v1.0.0_backup.db instance/ctf.db

# Verify integrity
python -c "import sqlite3; c=sqlite3.connect('instance/ctf.db'); print(c.execute('PRAGMA integrity_check').fetchone()[0])"
```

### Step 4 — Verify Migration Head

```bash
flask db current
# Expected after rollback to rc1: 8bce79803ffc (head)
# (v1.0.0 and v1.0.0-rc1 share the same migration head — no new migrations in stabilization)
```

### Step 5 — Run Test Suite

```bash
python -m pytest --tb=short -q
# Expected: 1609+ passed, 0 failed
```

### Step 6 — Restart Application

Follow the [startup runbook](./startup.md).

---

## Rollback Limitations

- If the v1.0.0 release introduced new migrations (it did NOT for this release), database rollback requires downgrade scripts.
- Application data created between v1.0.0 deployment and rollback may be lost if database is restored from backup.
- v1.0.0 and v1.0.0-rc1 share migration head `8bce79803ffc`, so no schema rollback is needed for this specific rollback path.

---

## Escalation Condition

Escalate if:
- Database backup is unavailable or integrity check fails
- `git checkout` introduces merge conflicts
- Test suite fails after rollback

---

## Audit Evidence to Retain

- Rollback authorization record (who authorized, when)
- Git commit before and after rollback
- Database backup used
- Test suite result after rollback
- Timestamp of rollback completion
