# Cyber Insurance Modeling Guide

## Overview

Cyber insurance modeling quantifies financial exposure from digital risk events and maps that exposure against active insurance policies to identify coverage gaps.

---

## Insurance Policies

Active policies are tracked via `InsurancePolicy`:

| Field | Description |
|-------|-------------|
| `provider` | Insurance carrier name |
| `coverage` | Total financial coverage (USD) |
| `deductible` | Policy deductible (USD) |
| `renewal_date` | Policy expiration / renewal deadline |

---

## Financial Exposure Estimation

The platform estimates downtime losses based on Business Impact Analysis (BIA):

```
estimated_loss = sum(bia.financial_impact × $100,000) per process
```

Default baseline exposure: **$250,000** (when no BIA data exists).

---

## Coverage Gap Analysis

```
coverage_gap = estimated_losses - current_coverage
```

| Situation | Recommended Action |
|-----------|-------------------|
| `coverage_gap > 0` | Acquire additional coverage |
| `coverage_gap ≤ 0` | Coverage is sufficient |

**Premium Estimate**: ~1.5% of coverage gap

**Deductible Recommendation**: ~5% of coverage gap

---

## Executive Copilot

The Executive Resilience AI can answer insurance questions:

```http
POST /api/v1/resilience/copilot
Authorization: Bearer <token>

{
  "question": "What is our estimated downtime loss?",
  "organization_id": 1
}
```

**Response:**
```json
{
  "question": "What is our estimated downtime loss?",
  "answer": "The estimated maximum downtime business loss exposure is $500,000.00..."
}
```

---

## API Usage

### Get Insurance Recommendations

```http
GET /api/v1/insurance?org_id=1
Authorization: Bearer <token>
```

**Response:**
```json
{
  "organization_id": 1,
  "estimated_losses": 500000.0,
  "current_coverage": 250000.0,
  "coverage_gap": 250000.0,
  "recommended_additional_coverage": 250000.0,
  "recommended_premium_estimate": 3750.0,
  "recommendations": ["Acquire additional $250,000.00 cyber risk transfer coverage."]
}
```

---

## Security Controls

- No real insurance APIs, brokers, or financial transactions connected
- All calculations are simulation-based and offline
- Tenant-isolated results via `organization_id`
- JWT authentication required
