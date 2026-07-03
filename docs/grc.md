# Governance, Risk & Compliance (GRC) Guide

This guide covers framework controls tracking and risk register.

---

## 1. Compliance Scoring Model
The system supports multiple security compliance frameworks:
- **ISO 27001:** Information security management systems.
- **NIST CSF:** Cybersecurity framework core functions.
- **CIS Controls:** Critical security control check lists.
- **MITRE ATT&CK:** Security defensive mitigations.

### Scoring formula:
$$\text{Score} = \left(\frac{\text{Passed Controls}}{\text{Total Controls}}\right) \times 100$$

---

## 2. API Endpoints

### List Gaps & Audits Findings
- **URL:** `/api/v1/audits`
- **Method:** `GET`
