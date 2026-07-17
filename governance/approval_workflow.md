# Approval Workflow — Cyber Defense Platform
# EthicBids Technologies™ | Business Governance

---

## 1. Approval Tiers

| Tier | Scope | Approvers |
|---|---|---|
| **Tier 1 — Operational** | Documentation, monitoring configs, runbook updates | Department Head |
| **Tier 2 — Technical** | Dependency updates, hotfix patches (CVSS < 7) | Engineering Lead + Security Lead |
| **Tier 3 — Security** | Security patches (CVSS ≥ 7), auth changes | CTO + Security Lead |
| **Tier 4 — Architecture** | Schema changes, API changes, new services | ARB (full board vote) |
| **Tier 5 — Executive** | Major releases, commercial terms, partnerships, M&A | Executive Committee |

---

## 2. SLA by Tier

| Tier | Normal SLA | Emergency SLA |
|---|---|---|
| Tier 1 | 24 hours | 4 hours |
| Tier 2 | 48 hours | 8 hours |
| Tier 3 | 5 business days | 4 hours |
| Tier 4 | 10 business days | 24 hours |
| Tier 5 | Board meeting cycle | 48 hours |

---

## 3. Production Change Approval Checklist

Before any change reaches production, the following must be confirmed:

- [ ] RFC document drafted and approved
- [ ] Architecture Review Board vote recorded
- [ ] Security review completed
- [ ] Regression suite passed (1609/1609)
- [ ] DOM certification passed (236/236)
- [ ] Staging deployment validated
- [ ] Rollback plan documented
- [ ] Change window scheduled
- [ ] Monitoring alerts armed
- [ ] Post-deploy validation plan confirmed

---

## 4. Escalation Path

```
Request → Department Review
    │ Rejected → Requester notified with reason
    │ Approved → Technical Review
    │     │ Rejected → RFC revision required
    │     │ Approved → ARB Review (if Tier 4+)
    │     │               │ Approved → Production Deployment
    │     │               │ Rejected → Feature deferred to v2.0
```
