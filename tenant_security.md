# CTF Arena Tenant Security Policy

Security guarantees and threat model for the multi-tenant SaaS edition (Phase 15).

---

## Tenant Isolation Model

CTF Arena v2 SaaS uses a **shared-database, shared-schema** multi-tenancy model with **service-layer isolation** enforcement.

### Key Guarantee

> Every database query that returns tenant-scoped data MUST pass through `TenantMixin.tenant_filter()` in the service layer. No SQLAlchemy session events or global hooks are used.

This design was chosen over session-level row filtering because:
1. It preserves query transparency — filters are visible in service code
2. It keeps test isolation clean — tests can set `g.current_org` via `TenantContext` without poisoning the session
3. It is compatible with SQLite (dev) and PostgreSQL (prod) without dialect-specific RLS features

---

## Threat Model

| Threat | Risk | Mitigation |
|---|---|---|
| Cross-tenant data read | Org A reads Org B's challenges/users | `tenant_filter()` enforced in all service reads |
| Subdomain spoofing | Attacker forges `Host` header to access another org | Resolver only sets `g.current_org`; auth is still required for all mutations |
| Slug enumeration | Attacker guesses valid subdomain slugs | Slugs are non-secret; data is still protected by auth + tenant filter |
| Quota bypass | User creates unlimited resources by crafting API calls | `QuotaService.check()` called before every create operation in API layer |
| Plan downgrade abuse | Org cancels plan but retains data | Cancellation only changes `status`; data is not deleted; next upgrade re-enables |
| Privilege escalation | Member changes own role | `change_role()` requires `actor_id` with at least `administrator` role in production guards |
| Audit log tampering | Malicious plugin modifies audit entries | `OrganizationAuditLog` has no `update()` method; records are append-only |

---

## TenantMixin Usage Rules

### DO

```python
# Correct: always filter by org_id in service layer
def get_org_challenges(org_id):
    return Challenge.tenant_filter(Challenge.query, org_id).all()

# Correct: use tenant_or_null to include legacy (NULL org_id) records
def get_all_challenges_for_tenant(org_id):
    return Challenge.tenant_or_null(Challenge.query, org_id).all()
```

### DON'T

```python
# WRONG: returns challenges from ALL organizations
def get_challenges():
    return Challenge.query.all()

# WRONG: relies on caller to remember to filter
def get_challenges(query):
    return query.all()
```

---

## OrganizationResolverMiddleware

The `OrganizationResolverMiddleware.resolve_tenant()` function runs as a `before_request` hook on every HTTP request:

1. Reads the `Host` header.
2. Extracts the subdomain (first part of the FQDN when the domain has ≥ 3 parts).
3. Looks up `Organization` by `slug`, filtering `is_deleted=False`.
4. Sets `g.current_org = org` (or `None` for the default/root context).

**Important**: The middleware only *resolves* the organization. It does NOT enforce authentication. All mutations require `@require_login` plus tenant verification in the API/service layer.

### Bypass in Tests

Tests use `TenantContext` to set `g.current_org` without an HTTP request:

```python
from app.middleware.tenant_middleware import TenantContext

def test_something(app):
    with app.app_context():
        org = Organization.query.filter_by(slug='myorg').first()
        with TenantContext(org):
            # g.current_org == org inside this block
            result = some_service_call()
```

---

## Billing State Machine Security

The billing state machine enforces allowed transitions:

```
trial     → active
active    → past_due
active    → cancelled
past_due  → active
past_due  → cancelled
cancelled → (no transitions — terminal state)
```

`OrganizationBilling.transition_to()` explicitly validates the transition and returns `(False, error_msg)` for invalid moves. This prevents:
- Resurrecting cancelled subscriptions (must re-subscribe via support)
- Skipping states (e.g., `trial → past_due` is blocked)

---

## Quota Security

`QuotaService.check()` is called in the API layer **before** any resource creation. The implementation:

1. Reads the current **live usage** from the database (not a cached counter)
2. Compares against `org.get_quota(resource)` (respects column-level overrides)
3. Returns `(allowed=False, ...)` if `used >= limit`
4. Enterprise plan (`limit == -1`) always returns `allowed=True`

Cached counters were deliberately avoided to prevent race-condition quota bypass attacks.

---

## Audit Log Integrity

`OrganizationAuditLog` records are:
- Written by services, never by API routes directly
- Never updated after creation (no `update()` path exists)
- Store actor `user_id` and `ip_address` for forensic tracing
- Store `details` as JSON for structured event data

All sensitive org events produce an audit entry:

| Event | Action Value |
|---|---|
| Organization created | `org_created` |
| Organization suspended | `org_suspended` |
| Member invited | `member_invited` |
| Member removed | `member_removed` |
| Role changed | `member_role_changed` |
| Plan changed | `plan_changed` |
| Billing status changed | `billing_status_changed` |
| Setting changed | `setting_changed` |

---

## Reporting Security Issues

Report cross-tenant data leaks or quota bypass vulnerabilities as **private GitHub security advisories**, not public issues.
