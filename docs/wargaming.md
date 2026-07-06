# Strategic War Gaming Guide

The **War Gaming Engine** provides offline crisis simulation scenarios to test response speed, tool orchestration, and playbook execution effectiveness.

## Engine Actions

1. **Simulate:** Runs a mock Red vs. Blue wargame. Outcomes are randomized for training purposes.
2. **Score:** Compiles technical outcome scores.
3. **Summarize:** Provides organizational summaries of total operations run, win/loss stats, and cumulative performance.

## Simulation API

- **Endpoint:** `GET /api/v1/wargames?org_id=<id>` (JWT Required)

```json
[
  {
    "id": 1,
    "scenario": "Ransomware Storm",
    "participants": 4,
    "score": 0.85,
    "result": "blue_win",
    "organization_id": 1
  }
]
```
