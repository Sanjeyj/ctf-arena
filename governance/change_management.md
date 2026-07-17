# Change Management Policy
# EthicBids Technologies™ | Business Governance

---

## 1. Change Classification

| Class | Examples | Approval Required |
|---|---|---|
| **Emergency Patch** | Critical security CVE | CTO + Security Lead |
| **Standard Patch** | Dependency update, minor bug | Engineering Lead |
| **Minor Release** | New non-breaking feature (v1.1) | Product Board |
| **Major Release** | Breaking changes, new architecture (v2.0) | Executive Committee |
| **Documentation** | Governance, marketing, legal docs | Department Head |
| **Infrastructure** | Deployment configs, monitoring | DevOps Lead |

---

## 2. Change Control Workflow

```
Request → RFC Draft → Architecture Review → Security Review
   → Regression Validation → Product Board Approval
   → Staging Deployment → Production Deployment
   → Post-Deploy Monitoring → Change Record Closed
```

---

## 3. RFC (Request for Change) Template

Every production change must have an approved RFC:

```markdown
# RFC-XXXX: [Title]
**Author**: [Name]
**Date**: [YYYY-MM-DD]
**Priority**: Critical / High / Medium / Low
**Type**: Emergency Patch / Standard Patch / Minor / Major

## Problem Statement
## Proposed Solution
## Impact Assessment (Scope, Risk, Rollback Plan)
## Testing Plan
## Approval Signatures
```

---

## 4. Production Freeze Policy (v1.0.0)

> **ACTIVE FREEZE**: The v1.0.0 codebase is frozen as of 2026-07-17.
> No changes are permitted to `app/`, `templates/`, `static/`, `migrations/`, `tests/`, or any production module without an approved RFC, security review, and regression certification.

Emergency security patches require:
1. CVE advisory with CVSS score ≥ 7.0
2. CTO and Security Lead approval (within 4 hours)
3. Regression suite re-run
4. DOM certification re-run
5. Hotfix version tag: `v1.0.1`, `v1.0.2`, etc.
