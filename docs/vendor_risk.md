# Third-Party Vendor Risk Management Guide

## Overview

Third-Party Risk Management (TPRM) identifies, assesses, and monitors security risks introduced through external vendors, cloud providers, and supply chain dependencies.

---

## Vendor Profiles

Each third-party vendor is tracked with:

| Field | Description |
|-------|-------------|
| `vendor_name` | Unique name of the supplier/partner |
| `service_type` | Category (SaaS, cloud, hardware, consulting, etc.) |
| `risk_score` | Composite risk rating (0–100, higher = riskier) |
| `contract_status` | `active`, `expired`, `under_review` |

---

## Vendor Assessments

Detailed compliance audits are recorded via `VendorAssessment`:

| Field | Description |
|-------|-------------|
| `assessment_score` | Overall audit score (0–100) |
| `compliance_score` | Regulatory/standards compliance score |
| `recommendations` | Findings and remediation suggestions |

### Risk Score Recalculation

After each assessment, the vendor's risk score is recalculated:

```
risk_score = 100 - (compliance_score × 0.5 + assessment_score × 0.5)
```

Higher compliance and assessment scores directly reduce the vendor risk.

---

## API Usage

### List Vendors

```http
GET /api/v1/vendors?org_id=1
Authorization: Bearer <token>
```

### Register a New Vendor

```http
POST /api/v1/vendors
Authorization: Bearer <token>

{
  "vendor_name": "AcmeSaaS Inc.",
  "service_type": "SaaS",
  "risk_score": 45.0,
  "organization_id": 1
}
```

---

## Risk Rating Tiers

| Score Range | Rating | Action |
|------------|--------|--------|
| 0–39 | 🟢 Low | Routine monitoring |
| 40–69 | 🟡 Medium | Quarterly audit |
| 70–100 | 🔴 High | Immediate reassessment |

---

## Security Controls

- No vendor integration APIs or live data connections
- All assessments are simulation-only
- Tenant-isolated data via `organization_id`
- JWT authentication enforced on all endpoints
