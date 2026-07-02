# Production Deployment Guide

This guide details best practices for running CTF Arena v2 in hostile production environments.

---

## 1. Stack Architecture

For staging and production, we recommend deploying behind a reverse proxy:

```
Competitor Client ──► HTTPS ──► Nginx Proxy ──► Gunicorn Web (Flask) ──► PostgreSQL DB
```

---

## 2. Hardening Environment Variables

Configure these settings in your `.env` file:

```ini
FLASK_ENV=production
SECRET_KEY=generate-a-strong-32-char-random-string
DATABASE_URL=postgresql://user:password@db-host:5432/ctfdb
SESSION_COOKIE_SECURE=True
PREFERRED_URL_SCHEME=https
TRUSTED_PROXIES=1
ALLOWED_HOSTS=ctf.example.com
```

---

## 3. Gunicorn Execution

Start Gunicorn with threaded workers:

```bash
gunicorn wsgi:application \
  --bind 127.0.0.1:5000 \
  --workers 4 \
  --threads 2 \
  --timeout 60
```
