# Decision Engine Guide

## Overview

The AI Decision Engine acts as the central reasoning core of the Autonomous Cyber Enterprise. It processes non-deterministic outputs from security agents, ranks confidence levels, and enforces human-in-the-loop validation for critical decisions.

---

## Decision Ledger

Every decision is logged in the `AutonomousDecision` model with:
- **decision_type**: The classification (e.g. Block IP, Demote Privilege).
- **confidence**: Value between `0.0` and `1.0` representing agent confidence.
- **recommendation**: Detailed text justification compiled by the agent.
- **approval_status**: Status of the human approval (`pending_approval`, `approved`, `rejected`).

---

## Verdict Thresholds

The engine evaluates actions based on the confidence index:

```
Verdict = "approve" if confidence >= 0.85 else "request_manual_review"
```

- **Confidence >= 0.85**: Recommended for automated execution.
- **Confidence < 0.85**: Marked for manual review.
- **Confidence < 0.70**: Requires multi-factor authorization.

---

## API Endpoints

### List Decisions

```http
GET /api/v1/decisions?org_id=1
Authorization: Bearer <token>
```

### Approve a Decision

```http
POST /admin/enterprise/decisions
```

Approved decisions are routed to the **RemediationService** to simulate self-healing actions.
