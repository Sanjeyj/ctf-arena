# =============================================================================
# CTF Arena v1.0.0 — Production Environment Documentation
# EthicBids Technologies™
# =============================================================================

# Production Environment Variables

## Overview

This document is the definitive reference for all environment variables
required to run CTF Arena v1.0.0 in a production environment.

| Symbol | Meaning |
|--------|---------|
| 🔴 REQUIRED | Application will not start without this variable |
| 🟡 RECOMMENDED | Should be set in production for security/performance |
| 🟢 OPTIONAL | Has a safe default; change only if needed |

---

## Core Application

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `SECRET_KEY` | 🔴 REQUIRED | — | Flask secret key for session signing and CSRF tokens. Generate: `python -c "import secrets; print(secrets.token_hex(64))"` |
| `FLASK_ENV` | 🔴 REQUIRED | `development` | Must be `production` in production. Controls debug mode, error pages, and logging verbosity. |
| `ADMIN_USER` | 🟡 RECOMMENDED | `admin` | Default administrator username seeded on `flask seed`. |
| `ADMIN_PASSWORD` | 🔴 REQUIRED | `ctf_admin_2024` | Default administrator password. **MUST be changed from default before first start.** |
| `APP_VERSION` | 🟢 OPTIONAL | `latest` | Docker image tag. Set to `1.0.0` for production pinning. |

---

## Database

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `DATABASE_URL` | 🔴 REQUIRED | `sqlite:///instance/ctf.db` | Full SQLAlchemy connection URL. Use PostgreSQL in production. Format: `postgresql://USER:PASS@HOST:PORT/DB` |
| `POSTGRES_DB` | 🟡 RECOMMENDED | `ctfarena` | PostgreSQL database name (used by docker-compose). |
| `POSTGRES_USER` | 🟡 RECOMMENDED | `ctfarena` | PostgreSQL username (used by docker-compose). |
| `POSTGRES_PASSWORD` | 🔴 REQUIRED | — | PostgreSQL password. Generate with a strong random value. |

### Security
- Use a dedicated database user with least privilege (SELECT, INSERT, UPDATE, DELETE only — no SUPERUSER).
- Enable SSL connections: append `?sslmode=require` to `DATABASE_URL`.
- Rotate database password every 90 days.

---

## Redis

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `REDIS_URL` | 🟡 RECOMMENDED | — | Full Redis URL for rate limiting. Format: `redis://:PASSWORD@HOST:PORT/DB` |
| `REDIS_PASSWORD` | 🟡 RECOMMENDED | — | Redis authentication password. |

### Notes
- Without Redis, in-memory rate limiting is used (resets on restart, not shared across workers).
- Redis must be reachable before the application starts.

---

## Networking & Proxy

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `TRUSTED_PROXIES` | 🟡 RECOMMENDED | `0` | Number of trusted reverse proxy hops. Set to `1` when behind a single Nginx instance. Required for accurate client IP detection. |
| `HTTP_PORT` | 🟢 OPTIONAL | `80` | Host HTTP port mapped to Nginx. |
| `HTTPS_PORT` | 🟢 OPTIONAL | `443` | Host HTTPS port mapped to Nginx. |
| `DOMAIN` | 🟡 RECOMMENDED | — | Production domain name (e.g., `arena.ethicbids.vercel.app`). Used in Nginx and Caddy configs. |

---

## Session & Cookies

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `SESSION_COOKIE_SECURE` | 🔴 REQUIRED | `False` | Must be `True` in production. Sends session cookie only over HTTPS. |
| `SESSION_COOKIE_HTTPONLY` | 🔴 REQUIRED | `True` | Prevents JavaScript from reading the session cookie. Do not change. |
| `SESSION_COOKIE_SAMESITE` | 🟡 RECOMMENDED | `Lax` | CSRF protection. Use `Strict` for maximum isolation. |

---

## File Uploads

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `MAX_CONTENT_LENGTH` | 🟢 OPTIONAL | `16777216` (16 MB) | Maximum upload size in bytes. Adjust for large challenge files. |

---

## Rate Limiting

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `RATE_LIMIT_LOGIN` | 🟡 RECOMMENDED | `5 per minute` | Login endpoint rate limit. Prevents brute-force attacks. |
| `RATE_LIMIT_SUBMIT` | 🟡 RECOMMENDED | `10 per minute` | Flag submission rate limit. |
| `RATE_LIMIT_API` | 🟡 RECOMMENDED | `60 per minute` | General API rate limit. |

---

## Gunicorn (WSGI Server)

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `GUNICORN_WORKERS` | 🟡 RECOMMENDED | `cpu*2+1` | Number of worker processes. Recommended: `2 * nproc + 1`. |
| `GUNICORN_TIMEOUT` | 🟢 OPTIONAL | `30` | Request timeout in seconds. Increase for long-running operations. |
| `GUNICORN_BIND` | 🟢 OPTIONAL | `127.0.0.1:8000` | Gunicorn bind address. Use `0.0.0.0:8000` in Docker. |
| `GUNICORN_WORKER_CLASS` | 🟢 OPTIONAL | `sync` | Worker class. Use `gevent` for SSE/WebSocket support. |
| `GUNICORN_LOG_LEVEL` | 🟢 OPTIONAL | `info` | Gunicorn log verbosity. Use `warning` in production. |

---

## Logging

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `LOG_LEVEL` | 🟢 OPTIONAL | `info` | Application log level. Options: `debug`, `info`, `warning`, `error`, `critical`. |

---

## Metrics & Monitoring

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `METRICS_ENABLED` | 🟡 RECOMMENDED | `False` | Enables the `/metrics` Prometheus endpoint. Set to `True` in production. |
| `GRAFANA_ADMIN_USER` | 🟢 OPTIONAL | `admin` | Grafana admin username. |
| `GRAFANA_PASSWORD` | 🔴 REQUIRED | — | Grafana admin password. Must be set. |
| `GRAFANA_ROOT_URL` | 🟢 OPTIONAL | — | Public Grafana URL (used for redirect links). |

---

## Email / SMTP (Optional)

| Variable | Status | Default | Description |
|----------|--------|---------|-------------|
| `MAIL_SERVER` | 🟢 OPTIONAL | — | SMTP hostname (e.g., `smtp.gmail.com`). |
| `MAIL_PORT` | 🟢 OPTIONAL | `587` | SMTP port. |
| `MAIL_USE_TLS` | 🟢 OPTIONAL | `True` | Enable STARTTLS. |
| `MAIL_USERNAME` | 🟢 OPTIONAL | — | SMTP authentication username. |
| `MAIL_PASSWORD` | 🟢 OPTIONAL | — | SMTP authentication password. |
| `MAIL_DEFAULT_SENDER` | 🟢 OPTIONAL | — | From address for outbound emails. |

---

## Secret Rotation Policy

| Secret | Rotation Frequency | Trigger |
|--------|--------------------|---------|
| `SECRET_KEY` | Every 180 days | On session invalidation acceptable |
| `ADMIN_PASSWORD` | Every 90 days | Immediately on suspected breach |
| `POSTGRES_PASSWORD` | Every 90 days | Requires DB restart |
| `REDIS_PASSWORD` | Every 90 days | Requires app restart |
| `GRAFANA_PASSWORD` | Every 90 days | |
| TLS Certificates | Every 90 days (auto via Certbot/Caddy) | On expiry warning |

---

## Quick Reference — Minimal Production `.env`

```bash
SECRET_KEY=<64-char-hex>
FLASK_ENV=production
ADMIN_PASSWORD=<strong-password>
DATABASE_URL=postgresql://ctfarena:<db-pass>@db:5432/ctfarena
POSTGRES_PASSWORD=<db-pass>
REDIS_URL=redis://:<redis-pass>@redis:6379/0
REDIS_PASSWORD=<redis-pass>
SESSION_COOKIE_SECURE=True
TRUSTED_PROXIES=1
METRICS_ENABLED=True
GRAFANA_PASSWORD=<grafana-pass>
DOMAIN=your-domain.com
```
