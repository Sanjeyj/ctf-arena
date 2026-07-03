# Corporate Policies Compliance Guide

This guide covers corporate security policies acknowledgements workflows.

---

## 1. Policy Mandates & Expirations
All corporate security policies are version-controlled:
1. Policies must be approved by the CISO board (`status='approved'`).
2. Staff members must log their acceptance through explicit acknowledgements mappings.

---

## 2. API Endpoints

### Fetch compliance maturity stats
- **URL:** `/api/v1/compliance`
- **Method:** `GET`
- **Response:**
  ```json
  {
    "compliance_score": 80.0,
    "total_controls": 10,
    "passed": 8,
    "failed": 2,
    "partial": 0
  }
  ```
