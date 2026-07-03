# Security Orchestration Mesh Guide

## Overview

The Security Orchestration Mesh coordinates complex multi-agent security response workflows. It binds events (triggers) to workflows, distributes tasks to digital worker bots, and monitors the overall pipeline health.

---

## Workflow Triggers

Workflows are initiated based on specific triggers:

| Event Trigger | Description | Targeted Agent |
|---------------|-------------|----------------|
| `on_incident` | Outage or security incident detected | SOC Agent |
| `on_threat_intel` | Reputational drift or indicators change | CTI Agent |
| `on_compliance_drift` | Governance framework score drop | Compliance Agent |

---

## API Endpoints

### List Workflows

```http
GET /api/v1/workflows?org_id=1
Authorization: Bearer <token>
```

### Trigger Workflows Manually

```http
POST /api/v1/tasks
Authorization: Bearer <token>

{
  "agent_id": 1,
  "task_type": "Auto-Triggered Response: on_incident",
  "priority": "high",
  "organization_id": 1
}
```

---

## Security Controls

- Enforces tenant isolation using standard `organization_id` queries.
- Limits agent execution threads to prevent orchestration loops.
