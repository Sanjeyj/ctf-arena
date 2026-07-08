# Startup Runbook

**Purpose**: Procedure for starting the Cyber Defense Platform (CDP) in development or staging environments.  
**Operating Mode**: SIMULATION-ONLY — no live network calls, no cloud mutations.

---

## Prerequisites

- Python 3.10+ installed
- Virtual environment activated
- `requirements.txt` dependencies installed
- Environment variables configured (see `docs/configuration_security_audit.md`)
- SQLite database present at `instance/ctf.db` (or configured `DATABASE_URL`)

---

## Safe Startup Procedure

### Step 1 — Activate Environment

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### Step 2 — Verify Migration Head

```bash
flask db current
# Expected: 8bce79803ffc (head)
```

If the head is not `8bce79803ffc`, run `flask db upgrade` before proceeding.

### Step 3 — Run Test Suite (Optional but Recommended)

```bash
python -m pytest --tb=short -q
# Expected: 1609+ passed, 0 failed
```

### Step 4 — Start the Application

```bash
# Development server (single-threaded, debug=False in staging)
flask run --host=0.0.0.0 --port=5000
```

Or using Gunicorn (production-grade staging):

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Step 5 — Verify Startup

```bash
# Check health endpoint
curl http://localhost:5000/health
# Expected: HTTP 200
```

---

## Expected Startup Warnings

The following warnings are expected and non-blocking:

- `[DockerService] Docker daemon unreachable — running in SIMULATION mode.` — Expected if Docker is not installed.
- `Using the in-memory storage for tracking rate limits` — Expected without a Redis backend.
- `Error loading enabled plugins: no such table: plugin_installations` — Non-fatal; table is created by migration.

---

## Verification

- Application responds on `http://localhost:5000`
- Admin interface accessible at `http://localhost:5000/admin/`
- API responds at `http://localhost:5000/api/v1/`

---

## Rollback

If startup fails:

1. Check `logs/error.log` for the stack trace.
2. Verify `flask db current` returns expected head.
3. Verify `requirements.txt` dependencies are all installed.
4. Restore `instance/ctf.db` from backup if database is corrupted.

---

## Escalation Condition

Escalate if:
- Application crashes on startup with unhandled exceptions
- Migration head does not match `8bce79803ffc` after `flask db upgrade`
- Database integrity check fails

---

## Audit Evidence to Retain

- `flask db current` output
- `flask run` startup log (first 50 lines)
- Timestamp of startup
