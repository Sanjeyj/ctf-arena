# Autonomous Agents Guide

## Overview

Autonomous agents represent the digital workforce layer of the Autonomous Cyber Enterprise. Deployed across the security orchestration mesh, these agents run non-deterministic security assessments, threat searches, and continuous compliance monitors.

---

## Agent Roles

The platform supports 5 native roles:

| Role | Focus Area | Matching Agent Trigger |
|------|------------|------------------------|
| **SOC Agent** | Real-time threat analysis & log monitoring | `on_incident` |
| **CTI Agent** | Feed ingestion and indicators lookups | `on_threat_intel` |
| **Compliance Agent** | Continuous compliance alignment & drift checks | `on_compliance_drift` |
| **Resilience Agent** | Business continuity checks & recovery drills | `on_resilience_drill` |
| **Executive Agent** | Goals reporting and AI copilot assessments | `on_executive_query` |

---

## API Usage

### Retrieve Active Agents

```http
GET /api/v1/agents?org_id=1
Authorization: Bearer <token>
```

### Deploy a New Agent

```http
POST /api/v1/agents
Authorization: Bearer <token>

{
  "name": "AuditBot-2000",
  "role": "Compliance Agent",
  "model": "gpt-4",
  "confidence": 0.95,
  "organization_id": 1
}
```

---

## Scheduler and Execution

Agents compile scheduled tasks through the **AutonomousAgentService**:
- **schedule**: Enqueues new tasks based on event triggers.
- **execute**: Invokes the LLM model to perform the work in simulation-only mode.
- **monitor**: Evaluates SLA success rates and logs execution latency.

---

## AI Safety Rules

- Agents operate strictly in **simulation mode**.
- No active system commands are executed on external hosts.
- Multi-tenant boundary isolation enforced via `organization_id`.
