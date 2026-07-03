# Global Threat Exchange Integration Guide

This guide details trust validation models for federated threat exchanges.

---

## 1. Trust Classification
Shared indicators are classified under three trust levels:
- `trusted`: Verified by trusted organizational partners.
- `verified`: Verified by threat intelligence analysts.
- `community`: Open threat intelligence feeds broadcast.

---

## 2. API Endpoints

### List shared indicators
- **URL:** `/api/v1/exchange`
- **Method:** `GET`
- **Query Parameter:** `trust_level` (Optional filter)
