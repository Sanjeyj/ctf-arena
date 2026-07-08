# Shutdown Runbook

**Purpose**: Procedure for safely shutting down the CDP in development or staging environments.

---

## Prerequisites

- Running CDP instance
- Access to the process or service manager

---

## Safe Shutdown Procedure

### Step 1 — Graceful Signal (Development Server)

Press `Ctrl+C` in the terminal running `flask run`. Flask's development server handles `SIGINT` gracefully.

### Step 2 — Graceful Shutdown (Gunicorn)

```bash
# Find the Gunicorn master PID
ps aux | grep gunicorn

# Send SIGTERM for graceful shutdown (waits for in-flight requests)
kill -SIGTERM <master_pid>
```

### Step 3 — Database Checkpoint (SQLite WAL Mode)

If the database was running in WAL mode:

```python
import sqlite3
conn = sqlite3.connect('instance/ctf.db')
conn.execute('PRAGMA wal_checkpoint(FULL)')
conn.close()
print('WAL checkpoint complete')
```

### Step 4 — Verify Clean Shutdown

- Confirm process is no longer running: `ps aux | grep flask`
- Confirm port is released: `netstat -an | grep 5000`

---

## Post-Shutdown Backup (Recommended)

```bash
# Create a timestamped backup after clean shutdown
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item instance/ctf.db "instance/ctf_shutdown_$ts.db"
```

---

## Rollback

If the application hangs during shutdown:

```bash
# Force kill (last resort)
kill -SIGKILL <pid>
```

Then verify database integrity:

```python
import sqlite3
conn = sqlite3.connect('instance/ctf.db')
print(conn.execute('PRAGMA integrity_check').fetchone()[0])
conn.close()
```

---

## Escalation Condition

Escalate if:
- Database integrity check fails after forced kill
- WAL checkpoint fails with an error
- Port is not released after shutdown

---

## Audit Evidence to Retain

- Shutdown timestamp
- WAL checkpoint result (if applicable)
- Post-shutdown backup file name and SHA-256
