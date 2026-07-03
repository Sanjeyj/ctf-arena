# Asset Management Inventory Integration Guide

This guide details Asset Management configuration and APIs.

---

## 1. Asset Types
Supported classifications include:
- `server`
- `workstation`
- `container`
- `application`
- `cloud`

---

## 2. API Endpoints

### List Assets
- **URL:** `/api/v1/assets`
- **Method:** `GET`

### Register discovered asset
- **URL:** `/api/v1/assets`
- **Method:** `POST`
- **JSON Payload:**
  ```json
  {
    "name": "Database-Core-01",
    "type_label": "server",
    "criticality": 9,
    "ip_address": "10.0.2.15"
  }
  ```
