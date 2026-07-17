# OWASP ASVS Compliance Mapping
# CTF Arena v1.0.0 — EthicBids Technologies™

This document maps platform security controls to the OWASP Application Security Verification Standard (ASVS) v4.0 Level 1 requirements.

---

## 1. ASVS Verification Control Map

| ASVS Section | Verification Requirement | Platform Control Implementation |
|--------------|-------------------------|---------------------------------|
| **V1 Architecture** | Threat modeling and secure design | Implemented. Blueprint enclaves separate participant portals from administration dashboards. |
| **V2 Authentication** | Password complexity and hashing | Passwords hashed using PBKDF2 with SHA-256 iterations. Basic length limits enforced on sign-up. |
| **V3 Session Management** | Session identifiers and cookies | Session tokens are randomly generated strings, marked with `HttpOnly`, `Secure`, and `SameSite=Lax` parameters. |
| **V4 Access Control** | Least privilege enforcement | Access to `/admin/*` routes requires the `Admin` or `Moderator` role mapped inside the context decorator. |
| **V5 Validation & Encoding**| XSS and SQL injection defenses | HTML escaping handled natively by the Jinja2 template engine. Inputs parsed via SQLAlchemy ORM. |
| **V12 File Uploads** | Secure uploads validation | File extensions validated against a whitelist; files stored with randomized names outside the web root. |
| **V13 API Security** | REST API controls | API endpoints protected by active rate limiting (via Flask-Limiter and Redis). |
