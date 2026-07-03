# Intelligence Trust Scoring Guide

## Overview

The Trust Network layer manages bilateral trust relationships between organizations
participating in the Global Security Intelligence Network. Trust scores determine
the weight given to shared intelligence reports and subscription feeds.

---

## Trust Score Model

Each `TrustNetwork` record represents a directed trust relationship:

- `source_org` → the organization extending trust
- `target_org` → the organization receiving trust
- `trust_score` → float `[0.0, 1.0]` representing trust level
- `status` → `pending` | `active` | `suspended` | `revoked`

---

## Status Transitions

| Condition | Status |
|---|---|
| Initially created | `pending` |
| Score >= 0.6 | `active` |
| Score < 0.2 | `suspended` |
| Manual revocation | `revoked` |

---

## Trust Service API

```python
# Create a new trust relationship
trust = TrustService.calculate('OrgA', 'OrgB', org_id=1)

# Validate a trust relationship
result = TrustService.validate(trust.id)
# Returns: {'valid': True, 'status': 'active', 'trust_score': 0.7, ...}

# Update trust score on new signal
updated = TrustService.update(trust.id, delta=+0.1)  # Positive signal
updated = TrustService.update(trust.id, delta=-0.3)  # Negative signal (incident)
```

---

## Trust in Practice

- Shared intelligence reports from `active` partners are weighted by their trust score
- `suspended` partners continue to receive shared intelligence but cannot send
- `revoked` partners are removed from all federation subscriptions
