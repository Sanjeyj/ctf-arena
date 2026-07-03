# Self-Healing Security Systems Guide

## Overview

The Self-Healing Security capability automates remediation actions to isolate threats and repair misconfigurations. All executions are simulated offline to prevent unintended side effects on real-world infrastructure.

---

## Remediation Logs

Remediation actions are logged via `RemediationAction` records:
- **action_type**: Description of remediation (e.g. Block Port, Rebuild Container).
- **severity**: Level of urgency (`low`, `medium`, `high`, `critical`).
- **status**: Status of self-healing (`pending`, `executing`, `completed`, `failed`).
- **execution_time**: Simulated run latency in seconds.

---

## Safety Guidelines

> [!CAUTION]
> The platform does not issue live system commands or configure actual infrastructure. All operations run in **simulation-only mode** to verify logic paths and playbook structures without hazard.

---

## API Endpoints

### List Remediation Actions

```http
GET /api/v1/remediation?org_id=1
Authorization: Bearer <token>
```

---

## Audit Trial Compliance

Remediation actions record execution timestamps and are fully auditable through the Executive dashboard.
