# Playbook Engine Orchestration Reference

This guide details the configuration and execution of SOAR playbooks in the Playbook Engine.

---

## 1. Action Definitions
A playbook defines a sequential list of steps:
- `investigate`: Query logs to build target scope.
- `triage`: Perform severity calculations and mapping.
- `contain`: Isolate target assets and revoke user tokens.
- `escalate`: Open a ticket case.
- `close`: Archive event logs.

---

## 2. API Endpoints

### List Playbooks
- **URL:** `/api/v1/playbooks`
- **Method:** `GET`

### Execute Playbook
- **URL:** `/api/v1/playbooks`
- **Method:** `POST`
- **JSON Payload:**
  ```json
  {
    "playbook_id": 1,
    "alert_id": 2
  }
  ```
- **Response (201 Created):** Returns execution logs detailing each active step execution status.
