# Vercel Environment Variables Document
# CTF Arena v1.0.0 — EthicBids Technologies™

This document outlines the environment variables that must be configured in the Vercel Dashboard under **Project Settings > Environment Variables** for CTF Arena v1.0.0.

---

## 1. Required Variables

| Variable Name | Production Value | Description |
|---|---|---|
| `FLASK_ENV` | `production` | Enables optimization hooks and limits debug output. |
| `SECRET_KEY` | *[Secure Random Hex]* | Session cookie signing key. |
| `DATABASE_URL` | `postgresql://...` | Connection URL for external PostgreSQL database. |
| `REDIS_URL` | `redis://...` | Connection URL for external Redis database (Rate limiting). |
| `ADMIN_PASSWORD` | *[Secure String]* | Default password seeded on database upgrade. |

---

## 2. Secure Cookie Configuration

Vercel forces HTTPS redirection on all domains. The following settings are required to prevent session leakage and enable cookie transmission:

* **SESSION_COOKIE_SECURE**: Must be set to `True`.
* **SESSION_COOKIE_HTTPONLY**: Must be set to `True` (blocks JavaScript read attempts).
* **SESSION_COOKIE_SAMESITE**: Recommended `Lax` (safeguards against CSRF attacks).
* **TRUSTED_PROXIES**: Set to `1` so the app parses client IPs correctly from Vercel's proxy headers.
