# CTF Arena SaaS SDK

Developer guide for building on the multi-tenant SaaS edition of CTF Arena (Phase 15).

---

## Overview

CTF Arena SaaS Edition hosts multiple isolated organizations (tenants) on a single platform. Each organization:

- Gets its own subdomain: `acme.ctfarena.local`
- Has fully isolated data (challenges, users, competitions, teams)
- Has a billing plan controlling resource quotas
- Has a 6-level role system for members

---

## Architecture

```
HTTP Request (acme.ctfarena.local)
    │
    ▼
OrganizationResolverMiddleware
  Reads Host header → resolves slug → sets g.current_org
    │
    ▼
Service Layer (OrganizationService / QuotaService / BillingService)
  Enforces tenant_filter(query, org_id) on all reads
    │
    ▼
TenantMixin models (User, Competition, Challenge, Team)
```

---

## Configuration

Organizations are resolved automatically from the `Host` header subdomain. In development, configure `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
127.0.0.1   acme.ctfarena.local
127.0.0.1   college.ctfarena.local
```

Then access: `http://acme.ctfarena.local:5000`

---

## REST API

All endpoints require an authenticated session (cookie-based login).

### Organization

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/organization` | Get current org info |
| POST | `/api/v1/organization` | Create a new organization |
| GET | `/api/v1/organization/members` | List org members |
| POST | `/api/v1/organization/invite` | Invite a user by username |

### Billing

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/billing` | Current billing state |
| POST | `/api/v1/billing/upgrade` | Upgrade plan |
| POST | `/api/v1/billing/cancel` | Cancel subscription |
| GET | `/api/v1/subscription` | Subscription + quota detail |

### Create Organization

```json
POST /api/v1/organization
Body: { "name": "ACME Security", "slug": "acme" }

Response 201:
{
  "message": "Organization created successfully.",
  "organization": { "id": 1, "name": "ACME Security", "slug": "acme", "plan_type": "free" }
}
```

### Invite Member

```json
POST /api/v1/organization/invite
Body: { "username": "jdoe", "role": "instructor" }

Response 200:
{ "message": "User invited successfully.", "member": { "id": 5, "user_id": 12, "role": "instructor" } }
```

### Upgrade Plan

```json
POST /api/v1/billing/upgrade
Body: { "plan": "professional" }

Response 200:
{ "message": "Plan updated successfully." }
```

### Get Subscription Details

```json
GET /api/v1/subscription

Response 200:
{
  "subscription": {
    "plan_type": "professional",
    "status": "active",
    "current_period_end": "2026-08-02T...",
    "quotas": {
      "users":        { "limit": 1000, "used": 23,  "available": 977 },
      "competitions": { "limit": 10,   "used": 2,   "available": 8 },
      "challenges":   { "limit": 500,  "used": 87,  "available": 413 },
      "containers":   { "limit": 50,   "used": 4,   "available": 46 },
      "ai_tokens":    { "limit": 500000, "used": 12000, "available": 488000 },
      "storage_mb":   { "limit": 10240, "used": 128, "available": 10112 }
    }
  }
}
```

---

## Member Roles

| Role | Level | Can Manage |
|---|---|---|
| `owner` | 0 (highest) | Everything |
| `administrator` | 1 | Members, settings, competitions |
| `manager` | 2 | Competitions, challenges |
| `instructor` | 3 | Challenges, hints |
| `member` | 4 | Compete only |
| `read_only` | 5 (lowest) | View only |

Check role permissions in service code:

```python
member = OrganizationMember.query.filter_by(org_id=..., user_id=...).first()
if member.can('manager'):
    # allowed
```

---

## Plans & Quotas

| Resource | Free | Professional | Enterprise |
|---|---|---|---|
| Users | 100 | 1,000 | Unlimited |
| Competitions | 1 | 10 | Unlimited |
| Challenges | 50 | 500 | Unlimited |
| Containers | 5 | 50 | Unlimited |
| AI Tokens | 10,000 | 500,000 | Unlimited |
| Storage | 512 MB | 10 GB | Unlimited |

Unlimited is represented internally as `-1`.

---

## Plugin Integration

Plugins can use `g.current_org` to scope their own data:

```python
from flask import g
from app.models.mixins import TenantMixin

# Service layer filtering example:
org_id = g.current_org.id if g.current_org else None
if org_id:
    challenges = TenantMixin.tenant_filter(Challenge.query, org_id).all()
else:
    challenges = Challenge.query.all()  # Default org fallback
```

---

## Quota Checking in Plugins

```python
from app.services.quota_service import QuotaService
from flask import g

if g.current_org:
    allowed, limit, used = QuotaService.check(g.current_org, 'challenges')
    if not allowed:
        return "Challenge quota reached", 429
```

---

## Admin Dashboard

Access organization management at `/admin/organization`:

- View all tenants (default context)
- View quota gauges and members (tenant context)
- Change billing plan at `/admin/organization/billing`
