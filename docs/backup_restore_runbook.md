# Backup & Restore Runbook (v1.0.0)

**Purpose**: Procedures for creating, verifying, and restoring CDP database backups.  
**Database**: SQLite (`instance/ctf.db`)  
**Safety**: Never overwrite the primary database during restore testing.

---

## Prerequisites

- Python 3.x installed
- Access to the `instance/` directory
- `flask db` CLI available in the virtual environment

---

## Backup Procedure

### Step 1 — Create Timestamped Backup

```bash
# From the repository root
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item instance/ctf.db "instance/ctf_backup_$ts.db"
```

Or using Python:

```python
import shutil, datetime
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2('instance/ctf.db', f'instance/ctf_backup_{ts}.db')
```

### Step 2 — Verify Backup Integrity

```python
import sqlite3
conn = sqlite3.connect('instance/ctf_backup_<ts>.db')
result = conn.execute('PRAGMA integrity_check').fetchone()[0]
conn.close()
assert result == 'ok', f"Integrity check failed: {result}"
print('Backup integrity: OK')
```

### Step 3 — Record Backup Hash

```python
import hashlib
h = hashlib.sha256(open('instance/ctf_backup_<ts>.db', 'rb').read()).hexdigest()
print('Backup SHA-256:', h)
# Record this hash for future verification
```

---

## Restore Procedure

> **⚠ WARNING**: Always restore into a SEPARATE test database. Never write directly over `instance/ctf.db` without a pre-existing backup.

### Step 1 — Restore to Separate Path

```python
import shutil
shutil.copy2('instance/ctf_backup_<ts>.db', 'instance/ctf_restored.db')
```

### Step 2 — Verify Restored DB Integrity

```python
import sqlite3
conn = sqlite3.connect('instance/ctf_restored.db')
ic = conn.execute('PRAGMA integrity_check').fetchone()[0]
tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
conn.close()
print('Integrity:', ic)
print('Table count:', tables)  # Expected: 249
```

### Step 3 — Verify Migration Head

Set `DATABASE_URL` to point to the restored DB and run:

```bash
set DATABASE_URL=sqlite:///instance/ctf_restored.db
flask db current
# Expected: 8bce79803ffc (head)
```

### Step 4 — Run Record Count Comparison

```python
import sqlite3
src = sqlite3.connect('instance/ctf.db')
rst = sqlite3.connect('instance/ctf_restored.db')
src_tables = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in src_tables:
    try:
        sc = src.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        rc = rst.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        if sc != rc:
            print(f'MISMATCH: {t} src={sc} rst={rc}')
    except Exception as e:
        print(f'SKIP: {t} ({e})')
src.close(); rst.close()
print('Record count comparison complete.')
```

---

## Rollback Considerations

- **SQLite ALTER TABLE**: SQLite does not support DROP COLUMN or constraint modification. Downgrades require table rebuild scripts.
- **Alembic Downgrade**: Safe downgrade path is from `8bce79803ffc` back to `ed9d81c062a8`. Always backup before downgrading.
- **Data Loss**: Downgrading across migrations that added columns will result in data loss for those columns.

---

## Escalation Condition

Escalate to senior engineer if:
- `PRAGMA integrity_check` returns anything other than `ok`
- Table count after restore is less than expected (249)
- Hash mismatch between original backup and restored copy
- `flask db current` shows a different migration head after restore

---

## Audit Evidence to Retain

- Backup file path and timestamp
- Backup SHA-256 hash
- `PRAGMA integrity_check` result
- Table count comparison output
- Migration head verification output
