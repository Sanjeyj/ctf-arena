# Tenant Isolation Incident Runbook

**Purpose**: Procedure for investigating and responding to suspected multi-tenant data isolation failures.

---

## Prerequisites

- Admin access to `instance/ctf.db`
- Ability to run diagnostic SQL queries
- Access to application logs

---

## Detection Signals

A tenant isolation incident may be indicated by:

1. A user from Organization A reports data belonging to Organization B
2. API response contains records with a different `organization_id` than the requesting tenant
3. Log entry shows a query without an `organization_id` filter on a tenant-scoped table
4. Cross-tenant ID reference in any model relationship

---

## Triage Procedure

### Step 1 — Identify the Affected Organization and Resource

From the report, determine:
- Reporting tenant: `org_id_A`
- Exposed tenant: `org_id_B` (if known)
- Affected resource type (e.g., `QuantitativeRiskScenario`, `ContagionScenario`)
- Affected API endpoint

### Step 2 — Inspect the Suspect Query

Search the service file for the endpoint's handler. Verify that all queries include `organization_id` filter:

```python
# Correct pattern
records = Model.query.filter_by(organization_id=org_id).all()

# Suspect pattern (missing filter)
records = Model.query.all()  # ← NO org filter
```

### Step 3 — Run Cross-Tenant Check Query

```python
import sqlite3
conn = sqlite3.connect('instance/ctf.db')

# Check for records accessible without org filter on a critical table
rows = conn.execute(
    "SELECT id, organization_id FROM quantitative_risk_scenarios LIMIT 20"
).fetchall()
for r in rows:
    print(r)
conn.close()
```

### Step 4 — Determine Blast Radius

- Was this a read-only leak or did a write occur?
- Which tenants are affected?
- How long was the endpoint unfiltered?

### Step 5 — Apply Fix

If a missing `organization_id` filter is confirmed:
1. Add the filter to the service query
2. Write a regression test to prevent recurrence
3. Run full test suite: `python -m pytest --tb=short -q`
4. Commit the fix with a clear message: `fix: add tenant isolation filter to <service>`

### Step 6 — Notify Affected Tenants

Per the platform's data governance policy, affected organizations must be notified if their data was exposed to another tenant.

---

## Governance Rule

> Cross-tenant data access is a **critical security violation**. All fixes must be reviewed and tested before deployment. Do NOT deploy untested isolation fixes.

---

## Escalation Condition

Escalate immediately to security team if:
- Data from one tenant was successfully written to another tenant's context
- More than one endpoint is found with missing tenant filters
- Exposure window exceeds 24 hours

---

## Audit Evidence to Retain

- Affected endpoint and service
- SQL query that caused the leak
- Affected `organization_id` values
- Timestamp of discovery and remediation
- Commit reference for the fix applied
- Test regression added
