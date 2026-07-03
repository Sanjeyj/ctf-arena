# Disaster Recovery Guide

## Overview

Disaster Recovery (DR) is the process of restoring IT operations after a catastrophic event. This platform provides structured recovery plan documentation, tabletop exercise tracking, and executive drill management.

---

## Disaster Recovery Plans

Plans are stored as `DisasterRecoveryPlan` records with:

| Field | Description |
|-------|-------------|
| `plan_name` | Unique plan identifier |
| `strategy` | Recovery approach (e.g. warm standby, cold backup) |
| `recovery_steps` | JSON ordered list of restoration procedures |
| `priority` | Integer ranking (1 = highest urgency) |
| `approval_status` | `draft`, `approved`, `retired` |

---

## Recovery Exercises

Resilience exercises are crucial for validating recovery readiness:

| Type | Description |
|------|-------------|
| `tabletop` | Discussion-based scenario walkthroughs |
| `simulation` | Partial or full environment recovery drill |
| `drill` | Timed execution of specific runbooks |

Exercises track:
- **results**: Outcomes observed during execution
- **lessons_learned**: Post-mortem findings for improvement
- **score**: Effectiveness rating (0–100)

---

## Crisis Event Coordination

Crisis events are declared and tracked using the `CrisisEvent` model:

### Declaring a Crisis

```http
POST /api/v1/crisis
Authorization: Bearer <token>

{
  "event_name": "Ransomware Outbreak — Production",
  "severity": "critical",
  "organization_id": 1
}
```

### Coordinating Response Updates

```http
GET /admin/resilience/crisis?org_id=1
```

### Resolving a Crisis

The system reduces the `impact_score` incrementally through coordination calls, and clears it fully on resolution.

---

## DR Tiers

| Tier | RTO Target | Strategy |
|------|-----------|----------|
| Tier 1 (Critical) | < 1 hour | Active-active failover |
| Tier 2 (High) | 1–4 hours | Warm standby |
| Tier 3 (Medium) | 4–24 hours | Cold backup |
| Tier 4 (Low) | > 24 hours | Manual recovery |

---

## Security Controls

- All endpoints are JWT-protected
- Tenant isolation enforced via `organization_id`
- No real-world disaster systems are connected — simulation only
