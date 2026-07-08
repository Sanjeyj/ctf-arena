# Incident Triage Runbook

**Purpose**: Procedure for investigating and responding to platform incidents.  
**Platform Mode**: SIMULATION-ONLY — no live infrastructure affected.

---

## Prerequisites

- Access to `logs/app.log`, `logs/error.log`, `logs/access.log`
- Access to `instance/ctf.db`
- Admin session or JWT token for API access

---

## Triage Procedure

### Step 1 — Identify Incident Type

Review `logs/error.log` for:
- `ERROR` level entries
- Stack traces
- Database errors (`OperationalError`, `IntegrityError`)
- Authentication failures (401/403 patterns in `logs/access.log`)

### Step 2 — Check Platform Health

```bash
# Via API (requires JWT)
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/service-health/

# Via admin dashboard
# Navigate to /admin/mission-control/
```

### Step 3 — Inspect Correlated Incidents

```python
# Directly query incident records
import sqlite3
conn = sqlite3.connect('instance/ctf.db')
incidents = conn.execute(
    "SELECT title, severity, status, detected_at FROM operational_incidents ORDER BY detected_at DESC LIMIT 10"
).fetchall()
for i in incidents:
    print(i)
conn.close()
```

### Step 4 — Determine Blast Radius

- Identify which `organization_id` is affected
- Confirm whether other tenants are unaffected (tenant isolation check)
- If multiple tenants are affected → platform-level incident

### Step 5 — Remediation

- For database errors: verify migration head, run `PRAGMA integrity_check`
- For auth failures: verify JWT secret key configuration
- For service errors: check `logs/app.log` for the triggering request

---

## Escalation Condition

Escalate immediately if:
- Cross-tenant data exposure is suspected
- AI service produces unmasked sensitive output
- Migration head mismatch detected after an incident

---

## Audit Evidence to Retain

- `logs/error.log` excerpt for the incident window
- Affected `organization_id`
- Incident record IDs from `operational_incidents` table
- Timeline of discovery, triage, and resolution
- Any commits applied as hotfixes
