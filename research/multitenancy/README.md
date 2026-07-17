# Multi-Tenancy Architecture — Research Initiative
# CTF Arena v2.0 — EthicBids Technologies™
# Research Phase | Not for Production

---

## 1. Vision

Transform the CTF Arena from a single-organization deployment into a full SaaS platform supporting multiple enterprise customers, each with isolated data, custom branding, billing tiers, and independent admin hierarchies.

---

## 2. Organization Hierarchy

```
EthicBids SaaS Platform
└── Tenant: Acme Corp
    ├── Organization: Acme Red Team
    │   ├── Team: Alpha Squad
    │   └── Team: Beta Squad
    └── Organization: Acme Blue Team
        └── Team: SOC Analysts
└── Tenant: FinSec Ltd
    └── Organization: Security Champions
```

---

## 3. Core Design Decisions

### A. Isolation Model
- **Database**: Shared database with `tenant_id` partition keys on all tables (row-level security via PostgreSQL RLS policies).
- **Schema isolation** (Enterprise): Separate PostgreSQL schema per tenant for maximum data isolation.
- **Kubernetes namespace isolation** for challenge ranges per tenant.

### B. Billing & Quotas

| Tier | Participants | Challenge Slots | AI Copilot | Price/mo |
|---|---|---|---|---|
| **Starter** | 50 | 25 | ❌ | $99 |
| **Professional** | 500 | 200 | ✅ (limited) | $499 |
| **Enterprise** | Unlimited | Unlimited | ✅ Full | Custom |

### C. Tenant Isolation Controls
- All DB queries automatically scoped by `tenant_id` via SQLAlchemy event listeners.
- Separate S3 buckets per tenant for challenge file uploads.
- Network isolation: Kubernetes NetworkPolicy per tenant namespace.

### D. Enterprise Management Portal
- Super-admin panel for EthicBids staff to manage tenants, view usage, trigger billing events.
- Tenant admin panel for customer IT admins to manage their organization hierarchy.

---

## 4. Implementation Roadmap

| Phase | Duration | Deliverable |
|---|---|---|
| **Alpha** | Q2 2027 | Tenant model, row-level security, basic billing |
| **Beta** | Q3 2027 | Enterprise management portal, quota enforcement |
| **GA** | Q4 2027 | Full SaaS launch with Stripe billing integration |

---

## 5. Status

**RESEARCH PHASE** — Production v1.0.0 single-tenant untouched.
