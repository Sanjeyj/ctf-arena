# Security Data Lake Integration Guide

This guide details logs normalization and Event Lake ingestion routes.

---

## 1. Normalization Format
Logs collected from SOC, CTI, and Cyber Range follow a standard format:
- `event_type`: Normalized category labels.
- `severity`: low, medium, high, critical.
- `source`: Collector tags labels.
- `payload`: JSON block containing logs key value details.

---

## 2. API Endpoints

### List Data Lake events
- **URL:** `/api/v1/events`
- **Method:** `GET`
- **Query Parameter:** `event_type` (Optional filter)
