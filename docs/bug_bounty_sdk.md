# Bug Bounty Platform integration Guide

This SDK guide explains the integration flow for the Bug Bounty platform of CTF Arena.

---

## 1. Authentication
Endpoints require JWT Bearer headers:
`Authorization: Bearer <jwt_token>`

---

## 2. API Endpoints

### List Submissions
- **URL:** `/api/v1/bounties`
- **Method:** `GET`
- **Response (200 OK):**
  ```json
  {
    "vulnerability_reports": [
      {
        "id": 1,
        "program_id": 2,
        "researcher_id": 5,
        "title": "SQL Injection in User Profile",
        "description": "Explaining parameters...",
        "cvss_score": 8.5,
        "severity": "high",
        "status": "submitted",
        "reputation_points": 85
      }
    ],
    "count": 1
  }
  ```

### Submit Vulnerability
- **URL:** `/api/v1/bounties`
- **Method:** `POST`
- **JSON Payload:**
  ```json
  {
    "program_id": 1,
    "researcher_id": 2,
    "title": "Reflected XSS in search",
    "description": "PoC payload details...",
    "cvss_score": 5.4,
    "org_id": 1
  }
  ```
- **Response (201 Created):** Returns the serialized `vulnerability_report` block.

---

## 3. Vulnerability States
Submissions undergo the following triage path:
1. **submitted**: Report received, pending validation.
2. **triaged**: Initial assessment completed, CVSS mapping updated.
3. **accepted**: Confirmed valid finding.
4. **duplicate**: Matching report already on file.
5. **resolved**: Bug fixed by target engineering team.
6. **rewarded**: Financial bounty reward paid out.
