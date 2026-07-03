# Risk Engine Integration Guide

This guide details calculations performed by the Risk Engine.

---

## 1. Risk calculation metrics

### Asset Risk
- **LOW:** Criticality score < 35.
- **MEDIUM:** Criticality score >= 35.
- **HIGH:** Criticality score >= 60.
- **CRITICAL:** Criticality score >= 80.

Formula incorporates base criticality score weighted by count of active alerts.

---

## 2. API Endpoints

### Query Risk Status
- **URL:** `/api/v1/risk`
- **Method:** `GET`
- **Response:**
  ```json
  {
    "organization_risk": "MEDIUM",
    "threat_risk": "LOW"
  }
  ```
