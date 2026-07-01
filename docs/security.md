# CTF Arena v2 — Security Guide

This document describes the security controls built into CTF Arena v2 and
best-practice recommendations for hardened deployments.

---

## Table of Contents

1. [Authentication & Session Security](#authentication--session-security)
2. [Password Policy](#password-policy)
3. [Rate Limiting & Brute-Force Protection](#rate-limiting--brute-force-protection)
4. [CSRF Protection](#csrf-protection)
5. [File Upload Security](#file-upload-security)
6. [File Download Security](#file-download-security)
7. [Database Safety](#database-safety)
8. [Secrets Management](#secrets-management)
9. [TLS & Transport Security](#tls--transport-security)
10. [Audit Logging](#audit-logging)
11. [Admin Hardening](#admin-hardening)
12. [Intentional Vulnerability Note](#intentional-vulnerability-note)
13. [Known Limitations & Future Work](#known-limitations--future-work)

---

## Authentication & Session Security

| Control | Implementation |
|---------|---------------|
| Password hashing | `bcrypt` with configurable cost factor |
| Session tokens | Flask signed cookies (HMAC-SHA256 via `SECRET_KEY`) |
| Cookie flags | `HttpOnly=True`; `Secure=True` when `SESSION_COOKIE_SECURE=True`; `SameSite=Lax` |
| Session timeout | `PERMANENT_SESSION_LIFETIME` (default 30 min idle) |
| Login history | Every login attempt (success or failure) is written to `LoginHistory` |

> **Critical:** Always set `SECRET_KEY` to a randomly generated string of at
> least 32 characters. A weak or default secret key allows session forgery.

```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Password Policy

Configurable via environment variables:

| Variable | Default | Effect |
|----------|---------|--------|
| `PASSWORD_MIN_LENGTH` | `8` | Minimum password length |
| `PASSWORD_REQUIRE_UPPER` | `True` | Must contain uppercase letter |
| `PASSWORD_REQUIRE_LOWER` | `True` | Must contain lowercase letter |
| `PASSWORD_REQUIRE_DIGIT` | `True` | Must contain digit |
| `PASSWORD_REQUIRE_SPECIAL` | `True` | Must contain special character |

Passwords are validated in `SessionService` before hashing. Rejected passwords
return a `400` response with a human-readable error.

---

## Rate Limiting & Brute-Force Protection

| Endpoint | Default limit | Variable |
|----------|---------------|----------|
| Login | 5 req/min | `RATE_LIMIT_LOGIN` |
| Flag submission | 10 req/min | `RATE_LIMIT_SUBMIT` |
| API (`/api/v1`) | 60 req/min | `RATE_LIMIT_API` |
| Global | 100 req/min | `RATE_LIMIT_GLOBAL` |

After `MAX_LOGIN_ATTEMPTS` (default 5) consecutive failures from the same IP,
the account is temporarily locked and an audit event is recorded.

Rate-limit state is stored in Redis if `REDIS_URL` is configured, otherwise
falls back to in-process memory (not suitable for multi-worker deployments).

---

## CSRF Protection

All HTML form `POST`, `PUT`, `PATCH`, `DELETE` requests require a valid CSRF
token, enforced by **Flask-WTF**.

- The token is injected into every template via `context_processors.py`.
- Forms must include `{{ csrf_token() }}` or use `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- AJAX requests must include the token in the `X-CSRFToken` header.
- CSRF is disabled only in the `TestingConfig` to allow automated test clients.

---

## File Upload Security

All uploaded challenge files are validated before saving:

1. **Extension allowlist** — only permitted extensions are accepted (configurable).
2. **MIME type check** — `python-magic` inspects the actual file header, not
   just the filename extension.
3. **Filename sanitisation** — `werkzeug.utils.secure_filename` strips path
   traversal characters and null bytes.
4. **Size limit** — `MAX_CONTENT_LENGTH` (default 16 MB) is enforced by Flask
   before the upload handler runs.
5. **Storage location** — files are stored in `uploads/`, outside the web root
   served by the static file handler.

---

## File Download Security

Download responses include the following headers:

```
Content-Disposition: attachment; filename="safe_name.ext"
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'none'
```

- `Content-Disposition: attachment` prevents the browser from rendering
  potentially malicious content inline.
- `X-Content-Type-Options: nosniff` prevents MIME-sniffing.
- A restrictive CSP header ensures no scripts in downloaded files are executed.

---

## Database Safety

### Graceful Rollback

All repository write operations use `safe_commit()`:

```python
def safe_commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
```

In addition, `app/__init__.py` registers a teardown handler that calls
`db.session.rollback()` at the end of every request where a transaction error
occurred. This prevents partial writes and connection pool poisoning.

### Parameterised Queries

All database queries use SQLAlchemy ORM methods or bound parameters.
Raw SQL is never used in application code outside of migration scripts.

### Least-Privilege DB User

When using PostgreSQL, create a dedicated database user with `SELECT`,
`INSERT`, `UPDATE`, `DELETE` privileges on the application schema only.
The migration user (which needs `CREATE TABLE`) should be separate.

---

## Secrets Management

| Secret | How to set |
|--------|-----------|
| `SECRET_KEY` | `.env` file or system environment |
| `ADMIN_PASSWORD` | `.env` file or system environment |
| `DATABASE_URL` | `.env` file or system environment |
| SSL certificates | Managed by Nginx / Let's Encrypt outside the app |

**Never commit secrets to version control.** The `.gitignore` already excludes
`.env` and `instance/`.

For container deployments, pass secrets as environment variables using Docker
secrets, Kubernetes secrets, or your cloud provider's secret manager
(e.g., AWS Secrets Manager, GCP Secret Manager).

---

## TLS & Transport Security

- Set `SESSION_COOKIE_SECURE=True` in production.
- Configure Nginx with TLS 1.2+ and a strong cipher suite.
- Enable HSTS: `add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;`
- Set `PREFERRED_URL_SCHEME=https` in the Flask config to generate correct URLs.

---

## Audit Logging

Security-relevant events are recorded in the `LoginHistory` table and the
audit log (accessible at `/admin/audit`):

| Event | Recorded fields |
|-------|----------------|
| Successful login | user, IP, timestamp, user agent |
| Failed login | attempted username, IP, timestamp |
| Account lockout | username, IP, timestamp |
| Admin action | admin user, action, target object, timestamp |
| Password change | user, timestamp |
| Challenge solve | user, challenge, IP, timestamp |

Audit log entries are read-only; they cannot be deleted through the UI.

---

## Admin Hardening

- Change the default admin password before going live.
- Consider placing `/admin` behind network-level access controls
  (VPN, IP allowlist in Nginx) in high-stakes competitions.
- The admin session is separate from participant sessions; admins can
  monitor the competition without interfering.
- Admin actions (user deletion, score reset) generate audit events.

---

## Intentional Vulnerability Note

> **For challenge organizers:** Challenge CH-06 ("Broken Vault") intentionally
> contains a SQL injection vulnerability for teaching purposes. This is isolated
> to the vault search endpoint and uses a **separate read-only SQLite connection**
> — it cannot affect the main application database.

Never expose CH-06 on the public internet without this isolation in place.

---

## Known Limitations & Future Work

| Issue | Status | Mitigation |
|-------|--------|-----------|
| `Query.get()` SQLAlchemy 2.0 deprecation | Open | Migrate to `Session.get()` in a future PR |
| Redis-less rate limiting is per-process | Open | Deploy Redis for multi-worker setups |
| No email-based 2FA | Planned | Use a TOTP library (e.g., `pyotp`) in a future milestone |
| Docker SDK errors not always surfaced to admin UI | Open | Improve `DockerService` error propagation |
