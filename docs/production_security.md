# Production Security Guide
# CTF Arena v1.0.0 — EthicBids Technologies™

## Overview

This document defines the security hardening requirements and recommendations for
running CTF Arena v1.0.0 in a production environment. All controls must be
verified before public exposure.

---

## 1. TLS / HTTPS

### Requirements
- **TLS 1.2 minimum**; TLS 1.3 preferred. Disable TLS 1.0 and 1.1.
- Use **ECDSA or RSA 2048+** certificates. Prefer ECDSA P-256 for performance.
- **Certificate sources** (in priority order):
  1. Caddy (automatic Let's Encrypt — recommended)
  2. Certbot (`certbot --nginx -d your-domain.com`)
  3. Commercial CA for compliance requirements

### Cipher Suite Recommendations
```
ECDHE-ECDSA-AES256-GCM-SHA384
ECDHE-RSA-AES256-GCM-SHA384
ECDHE-ECDSA-CHACHA20-POLY1305
ECDHE-RSA-CHACHA20-POLY1305
ECDHE-ECDSA-AES128-GCM-SHA256
ECDHE-RSA-AES128-GCM-SHA256
```

### Validation
```bash
# Test TLS configuration
curl -vI https://your-domain.com

# External scan
ssllabs.com/ssltest — target grade A or A+
```

---

## 2. HTTP Security Headers

All headers are applied at the Nginx/Caddy/Traefik layer. Required set:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS for 1 year |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Block clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Disable sensitive APIs |
| `Content-Security-Policy` | See below | Prevent XSS / injection |

### Content Security Policy

```
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com;
img-src 'self' data:;
connect-src 'self';
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

> [!NOTE]
> `'unsafe-inline'` is required for the current UI design system. Future versions should migrate to nonce-based CSP.

---

## 3. Secure Cookies

Configure the following in the production `.env`:

```bash
SESSION_COOKIE_SECURE=True      # HTTPS-only cookie transmission
SESSION_COOKIE_HTTPONLY=True    # No JavaScript access to session
SESSION_COOKIE_SAMESITE=Lax    # CSRF protection (use Strict for maximum isolation)
```

> [!WARNING]
> `SESSION_COOKIE_SECURE=False` in production is a critical vulnerability. The application will function but session cookies will transmit over HTTP.

---

## 4. HSTS Preload

After verifying the site serves only HTTPS:

1. Set `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
2. Submit domain to https://hstspreload.org/
3. Preload takes 1–4 weeks to propagate.

> [!CAUTION]
> HSTS preload is **permanent**. Only enable when you are certain the domain will always serve HTTPS.

---

## 5. Rate Limiting

Two-layer rate limiting is implemented:

| Layer | Location | Controls |
|-------|----------|---------|
| Application | Flask-Limiter | Per-route limits enforced in Python |
| Network | Nginx / Traefik | IP-based limits before requests reach app |

### Production Recommendations

| Endpoint | Limit | Rationale |
|----------|-------|-----------|
| `/login` | 5 req/min | Brute-force protection |
| `/admin/login` | 3 req/min | Admin credential protection |
| `/submit/*` | 10 req/min | Anti-cheating |
| `/api/*` | 60 req/min | API fair use |
| `/register` | 3 req/min | Account creation spam |

---

## 6. Secret Management

### Requirements
- `SECRET_KEY` must be **at least 64 random hex characters**.
- Never commit `.env.production` to version control.
- Use environment injection via Docker secrets, Vault, or GitHub Actions Secrets.

### Generation Commands
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(64))"

# Database password
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Redis password
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### `.gitignore` — Verify these are excluded
```
.env
.env.production
*.env
production.env
```

---

## 7. CSRF Protection

Flask-WTF CSRF protection is enabled globally. All form submissions include
a `csrf_token` hidden field. The token is:
- Tied to the session
- Rotated on every form render
- Verified server-side on POST/PUT/DELETE requests

**Do not disable CSRF protection** (`WTF_CSRF_ENABLED=False`) in any environment.

---

## 8. JWT Recommendations (API tokens)

The platform does not currently issue JWTs to participants. If future
API token issuance is added:
- Use `HS256` minimum; prefer `RS256` for asymmetric verification
- Token lifetime: 1 hour (access), 7 days (refresh)
- Store refresh tokens server-side (not in localStorage)
- Rotate signing keys every 180 days

---

## 9. Backup Encryption

All database backups must be encrypted at rest:

```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup.sql.gz

# Decrypt backup
gpg --decrypt backup.sql.gz.gpg | gunzip | psql -U ctfarena ctfarena
```

Store backup encryption keys separately from backup storage.

---

## 10. Network Isolation

Use Docker's internal network for backend services:

- `backend` network: app ↔ db ↔ redis ↔ prometheus ↔ grafana (internal, not routable)
- `frontend` network: nginx ↔ app (routable)
- Only Nginx ports (80, 443) are exposed to the host.

Never expose PostgreSQL (5432) or Redis (6379) ports to the host.

---

## 11. Non-Root Execution

The application container runs as UID 1001 (non-root).
Verify with:
```bash
docker exec ctf-arena-app whoami
```

Expected: `ctfarena` or UID 1001.

---

## 12. Production Security Checklist

| Control | Required | Verified |
|---------|----------|----------|
| TLS 1.2+ enforced | ✅ | ☐ |
| HTTP redirects to HTTPS | ✅ | ☐ |
| HSTS header present | ✅ | ☐ |
| CSP header present | ✅ | ☐ |
| X-Frame-Options: DENY | ✅ | ☐ |
| X-Content-Type-Options: nosniff | ✅ | ☐ |
| Referrer-Policy set | ✅ | ☐ |
| SESSION_COOKIE_SECURE=True | ✅ | ☐ |
| SECRET_KEY is random 64+ chars | ✅ | ☐ |
| ADMIN_PASSWORD changed from default | ✅ | ☐ |
| POSTGRES_PASSWORD set (not empty) | ✅ | ☐ |
| REDIS_PASSWORD set | ✅ | ☐ |
| Database not exposed to host | ✅ | ☐ |
| Redis not exposed to host | ✅ | ☐ |
| App runs as non-root | ✅ | ☐ |
| Rate limiting active | ✅ | ☐ |
| CSRF enabled | ✅ | ☐ |
| Backups encrypted | ✅ | ☐ |
| .env.production not in git | ✅ | ☐ |
| SSL Labs grade A or A+ | ✅ | ☐ |
