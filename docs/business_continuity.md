# Business Continuity Management (BCM) Guide

## Overview

Business Continuity Management (BCM) ensures the organization can maintain or rapidly resume critical functions after a disruptive event. This platform implements BCM as a structured data-driven capability.

---

## Core Concepts

### Business Process Registry

Every enterprise process that is essential to operations is tracked:

- **Criticality Levels**: `low`, `medium`, `high`, `critical`
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime (hours)
- **RPO (Recovery Point Objective)**: Maximum tolerable data loss window (hours)

### Business Impact Analysis (BIA)

Each process is assessed across three impact dimensions:

| Dimension | Scale | Meaning |
|-----------|-------|---------|
| `financial_impact` | 1–5 | Financial risk per hour of downtime |
| `operational_impact` | 1–5 | Workflow disruption severity |
| `reputation_impact` | 1–5 | Brand/trust damage exposure |

### Disaster Recovery Plans (DRP)

DRPs are compiled per business process tier, featuring:

- **strategy**: Warm standby, active-active, cold backup, etc.
- **recovery_steps**: Ordered JSON steps to restore services
- **priority**: Numeric tier (1 = highest)
- **approval_status**: `draft` → `approved` → `retired`

---

## API Usage

### List Business Processes

```http
GET /api/v1/resilience/processes?org_id=1
Authorization: Bearer <token>
```

### Register a New Process

```http
POST /api/v1/resilience/processes
Authorization: Bearer <token>

{
  "name": "Payment Processing Gateway",
  "owner": "Finance Team",
  "criticality": "critical",
  "rto": 1.0,
  "rpo": 0.5,
  "organization_id": 1
}
```

### Evaluate RTO Compliance (via Admin API)

```http
GET /admin/resilience/bcp?org_id=1
```

---

## RTO/RPO Evaluation Logic

The BCM service flags a process as **non-compliant** if:
- **RTO violation**: `status == 'active'` AND `rto <= 2.0 hours` without automated failover verified.
- **RPO violation**: `status == 'active'` AND `rpo <= 1.0 hour` without database replication confirmed.

---

## Security Controls

- Endpoints protected via **JWT Bearer tokens**
- Multi-tenant isolation via `organization_id` query filtering
- No external dependencies — all calculations performed offline
