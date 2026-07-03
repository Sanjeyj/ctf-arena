# Executive AI Copilot Guide

This guide details questions handled by the Executive AI Copilot.

---

## 1. Questions Supported
Executive users can query the copilot assistant:
1. **Risk:** *"What is our current risk?"*
2. **Incidents:** *"Which incidents are active?"*
3. **Critical Assets:** *"What assets are critical?"*
4. **Training Gaps:** *"What training gaps exist?"*

---

## 2. API Endpoints

### Query Executive Posture
- **URL:** `/api/v1/executive`
- **Method:** `GET`
- **Response:**
  ```json
  {
    "summary": {
      "open_incidents": 2,
      "risk_score": 45.0,
      "asset_health": 98.5,
      "training_status": "90% complete",
      "threat_level": "LOW"
    }
  }
  ```
