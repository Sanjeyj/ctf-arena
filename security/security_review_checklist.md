# Security Review Checklist
# CTF Arena v1.0.0 — EthicBids Technologies™

Use this checklist to perform security code reviews and configuration audits prior to any production releases or version tags.

---

## 1. Authentication & Session

- [ ] `FLASK_ENV` is set to `production`.
- [ ] `SECRET_KEY` is a minimum 64-character random string.
- [ ] `SESSION_COOKIE_SECURE` is explicitly set to `True`.
- [ ] `SESSION_COOKIE_HTTPONLY` is set to `True`.
- [ ] User passwords are hashed using `pbkdf2:sha256` or equivalent secure algorithm.
- [ ] Default passwords for `admin`, `db`, and `redis` are changed.

---

## 2. Input Validation & CSRF

- [ ] CSRF tokens are validated on all POST, PUT, and DELETE routes.
- [ ] File uploads validate file extension extensions against a strict whitelist.
- [ ] Input strings are sanitized to prevent XSS before rendering in HTML templates.
- [ ] No SQL queries are constructed using raw string concatenation.

---

## 3. Infrastructure & Network

- [ ] Docker container is running under a non-root user account (UID 1001).
- [ ] Application files are mounted as read-only inside the container.
- [ ] Rate limits are active on authentication and submission routes.
- [ ] Host firewall drops traffic to database and Redis ports from external interfaces.
- [ ] TLS certificate is active and scores A or A+ on SSL Labs.
