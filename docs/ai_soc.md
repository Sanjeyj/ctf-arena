# AI SOC Analyst Integration Guide

This guide details the AI SOC Analyst platform integration of CTF Arena.

---

## 1. Authentication
All operations require a standard JWT Bearer header:
`Authorization: Bearer <jwt_token>`

---

## 2. API Endpoints

### List AI Analysts
- **URL:** `/api/v1/agents`
- **Method:** `GET`

### Configure/Deploy AI Analyst
- **URL:** `/api/v1/agents`
- **Method:** `POST`
- **JSON Payload:**
  ```json
  {
    "name": "SOC_Analyst_Beta",
    "role": "analyst",
    "confidence": 0.90,
    "model": "gemini-2.0-pro"
  }
  ```

---

## 3. Automated Triage Capabilities
Deployed AI agents monitor the incoming security events queue and execute:
1. **Severity Prediction**: Classifies threat levels using event parameters.
2. **MITRE ATT&CK Mapping**: Matches alerts to TTP categories.
3. **Timeline Generation**: Summarizes incident actions chronologically.
