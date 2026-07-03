# Security Research & CTI API Reference

Welcome to the CTI Integration developer documentation. All endpoints are secured via JSON Web Tokens (JWT).

---

## Authorization
Authentication uses standard JWT Bearer tokens in the HTTP Header:
`Authorization: Bearer <jwt_token>`

Get a test token via:
- **URL:** `/api/v1/research/token`
- **Method:** `POST`
- **JSON Payload:** `{"username": "admin"}`
- **Response (200 OK):** `{"token": "<jwt_token>"}`

---

## 1. Threat Actor Intelligence API

### List Threat Actors
- **URL:** `/api/v1/threat-actors`
- **Method:** `GET`
- **Response (200 OK):**
  ```json
  {
    "threat_actors": [
      {
        "id": 1,
        "name": "APT29",
        "aliases": ["Cozy Bear", "Office Monkeys"],
        "country": "Russia",
        "motivation": "espionage",
        "sophistication": "state-sponsored"
      }
    ],
    "count": 1
  }
  ```

### Create Threat Actor
- **URL:** `/api/v1/threat-actors`
- **Method:** `POST`
- **JSON Payload:**
  ```json
  {
    "name": "APT39",
    "aliases": "Chafer",
    "country": "Iran",
    "motivation": "espionage",
    "sophistication": "state-sponsored"
  }
  ```

---

## 2. Campaign Tracking API

### List Campaigns
- **URL:** `/api/v1/campaigns`
- **Method:** `GET`

### Create Campaign
- **URL:** `/api/v1/campaigns`
- **Method:** `POST`
- **JSON Payload:**
  ```json
  {
    "actor_id": 1,
    "name": "Operation Windigo",
    "target_sector": "Healthcare",
    "description": "Multi-stage phishing campaign",
    "malware_used": "Cobalt Strike, Mimikatz",
    "techniques_used": "T1190, T1078"
  }
  ```

---

## 3. Static Malware Analysis API

### Analyze Artifact
Trigger static metadata parser uploader.
- **URL:** `/api/v1/malware/analyze`
- **Method:** `POST`
- **Form Data:**
  - `file`: (Binary upload file)
  - `family` (query param, optional): Target malware family designation

---

## 4. CTI Research Reports API

### List Reports
- **URL:** `/api/v1/reports`
- **Method:** `GET`

### Create Research Report
- **URL:** `/api/v1/reports`
- **Method:** `POST`
- **JSON Payload:**
  ```json
  {
    "title": "APT29 target profiling",
    "executive_summary": "Summary text",
    "technical_analysis": "Technical reversing notes",
    "iocs": ["evil.c2.domain.com"],
    "mitre_techniques": ["T1190"],
    "recommendations": "Apply firewall blocks"
  }
  ```
