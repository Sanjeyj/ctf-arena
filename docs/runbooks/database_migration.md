# Database Migration Runbook

**Purpose**: Procedures for applying, verifying, and rolling back Alembic database migrations.  
**Current Head**: `8bce79803ffc`  
**Migration Tool**: Flask-Migrate (Alembic)

---

## Prerequisites

- Virtual environment activated
- `flask` CLI available
- Database backup created before any migration operation
- `FLASK_APP` environment variable set

---

## Pre-Migration Checklist

1. ✅ Create a timestamped database backup
2. ✅ Verify current migration head: `flask db current`
3. ✅ Confirm no uncommitted application code changes: `git status`
4. ✅ Run test suite to establish baseline: `python -m pytest --tb=short -q`

---

## Applying Migrations (Upgrade)

```bash
# 1. Verify current state
flask db current

# 2. Show pending migrations
flask db history --indicate-current

# 3. Apply all pending migrations
flask db upgrade

# 4. Verify new head
flask db current
# Expected: 8bce79803ffc (head) for v1.0.0
```

---

## Rolling Back a Migration (Downgrade)

> ⚠ **WARNING**: Always backup the database before downgrading. Rollback may cause data loss.

```bash
# Downgrade one revision
flask db downgrade -1

# Downgrade to a specific revision
flask db downgrade ed9d81c062a8

# Verify rollback
flask db current
```

---

## Creating a New Migration (v1.1+ Only)

> **DO NOT create new migrations for v1.0.0. This section is for future maintenance only.**

```bash
# After modifying models
flask db migrate -m "descriptive_migration_name"

# Review the generated migration file in migrations/versions/
# Then apply
flask db upgrade
```

---

## Migration Chain Verification

```bash
# List full history
flask db history

# Check for multiple heads (should be exactly one)
flask db heads
# Expected: single line with (head)
```

---

## Verification

After any migration operation:

1. `flask db current` shows expected head
2. `python -m pytest --tb=short -q` passes all tests
3. Table count in `instance/ctf.db` matches expected (249 for v1.0.0)

---

## Escalation Condition

Escalate if:
- `flask db heads` shows multiple heads (branch conflict)
- `flask db upgrade` raises an `OperationalError`
- Test count drops below 1609 after migration
- Database integrity check fails after migration

---

## Audit Evidence to Retain

- Pre-migration backup path and SHA-256
- `flask db current` output before and after
- `flask db history` output
- Test suite result after migration
