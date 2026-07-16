# Security Architecture — Cyber Defense Platform v2.0

## 1. Zero Trust Architecture (ZTA) Controls

CDP v2.0 implements a comprehensive security model based on ZTA principles.

```
[Request] ──> [APIGateway (JWT validation)] ──> [Service (RBAC & Tenant Check)] ──> [Encrypted DB]
```

---

## 2. Hardening Measures

### 2.1 Multi-Tenancy Isolation
- **Logical Segregation**: Tenant isolation is enforced at the service level using middleware. Database queries require an `organization_id` parameter to prevent cross-tenant data leakage.
- **Access Verification**: The database session context is updated per request to restrict operations to the tenant's data scope.

### 2.2 Network Security & Authentication
- **Secure JWT Authentication**: APIs require signatures verified with HMAC-SHA256 or RS256 algorithms. Token lifetimes are limited to 15 minutes.
- **CSRF & Cookie Protection**: Session cookies default to `HttpOnly` and `SameSite=Strict`. State-changing endpoints require custom validation tokens.

### 2.3 AI Safety Guardrails
- **Prompt Sanitization**: Real-time scanners inspect input payloads for prompt injection vectors.
- **Sensitive Data Masking**: Outbound text blocks are parsed using pattern matching to mask database keys, user passwords, and CTF flags.
