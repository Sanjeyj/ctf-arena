# CTF Arena v2 — Deployment Guide

This guide covers local development, Docker, and production deployment options.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development (venv)](#local-development-venv)
3. [Environment Variables](#environment-variables)
4. [Database Setup and Migrations](#database-setup-and-migrations)
5. [Docker (single container)](#docker-single-container)
6. [Docker Compose (dev stack)](#docker-compose-dev-stack)
7. [Production Deployment (Gunicorn + Nginx)](#production-deployment-gunicorn--nginx)
8. [Cloud Deployment (Render.com)](#cloud-deployment-rendercom)
9. [Security Checklist](#security-checklist)

---

## Prerequisites

| Requirement | Minimum version |
|-------------|----------------|
| Python | 3.10 |
| pip | 23+ |
| SQLite **or** PostgreSQL | 3.35+ / 14+ |
| Redis *(optional, for rate-limiter)* | 6.2+ |
| Docker *(optional)* | 24+ |

---

## Local Development (venv)

```bash
# 1. Clone the repository
git clone https://github.com/Sanjeyj/ctf-arena.git
cd ctf-arena

# 2. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your local environment file
cp .env.example .env
# Edit .env and set at minimum: SECRET_KEY, ADMIN_PASSWORD

# 5. Initialise / migrate the database
flask db upgrade

# 6. (One-time) Generate the steganography challenge image
python make_stego.py

# 7. Start the development server
flask run --host=0.0.0.0 --port=5000
# or
python run.py
```

Open `http://localhost:5000` in your browser.

> **Tip:** The admin panel is at `http://localhost:5000/admin`.  
> Default credentials: `admin` / `ctf_admin_2024` — **change these in `.env`!**

---

## Environment Variables

Copy `.env.example` to `.env` and customise the values below.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `ctf_super_secret_2024` | Flask session secret — **change in production** |
| `ADMIN_USER` | `admin` | Admin panel username |
| `ADMIN_PASSWORD` | `ctf_admin_2024` | Admin panel password — **change in production** |
| `DATABASE_URL` | `sqlite:///instance/ctf.db` | SQLAlchemy DB URI (`sqlite://` or `postgresql://`) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL for rate limiting |
| `FLASK_ENV` | `development` | `development`, `staging`, or `production` |
| `MAX_CONTENT_LENGTH` | `16777216` | Max upload size in bytes (16 MB) |
| `SESSION_LIFETIME_SECONDS` | `1800` | Idle session timeout (30 min) |
| `SESSION_COOKIE_SECURE` | `False` | Set `True` when using HTTPS |
| `TRUSTED_PROXIES` | `0` | Number of trusted reverse-proxy hops |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hostnames |
| `RATE_LIMIT_LOGIN` | `5 per minute` | Login endpoint rate limit |
| `RATE_LIMIT_SUBMIT` | `10 per minute` | Flag submission rate limit |
| `RATE_LIMIT_API` | `60 per minute` | `/api/v1` rate limit |
| `RATE_LIMIT_GLOBAL` | `100 per minute` | Global rate limit |
| `PASSWORD_MIN_LENGTH` | `8` | Minimum password length |
| `PASSWORD_REQUIRE_UPPER` | `True` | Require uppercase letter |
| `PASSWORD_REQUIRE_LOWER` | `True` | Require lowercase letter |
| `PASSWORD_REQUIRE_DIGIT` | `True` | Require digit |
| `PASSWORD_REQUIRE_SPECIAL` | `True` | Require special character |
| `MAX_LOGIN_ATTEMPTS` | `5` | Lockout threshold |
| `METRICS_ENABLED` | `True` | Toggle platform metrics collection |

---

## Database Setup and Migrations

CTF Arena uses **Flask-Migrate** (Alembic) for schema management.

```bash
# First-time initialisation (only needed once per fresh install)
flask db init
flask db migrate -m "initial schema"
flask db upgrade

# After pulling new code with model changes
flask db upgrade

# Downgrade to the previous revision
flask db downgrade
```

### Using PostgreSQL

```bash
# Install the driver
pip install psycopg2-binary

# Set DATABASE_URL in .env
DATABASE_URL=postgresql://ctf_user:password@db:5432/ctfdb
```

---

## Docker (single container)

The included `Dockerfile` uses `python:3.11-slim` and runs Gunicorn.

```bash
# Build
docker build -t ctf-arena:latest .

# Run (SQLite, default)
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY=changeme \
  -e ADMIN_PASSWORD=changeme \
  -v $(pwd)/instance:/app/instance \
  --name ctf-arena \
  ctf-arena:latest

# Stop
docker stop ctf-arena && docker rm ctf-arena
```

> The `/app/instance` volume persists the SQLite database across container restarts.

---

## Docker Compose (dev stack)

The bundled `docker-compose.yml` starts a single-service stack.
For a full production stack with PostgreSQL and Redis, use:

```yaml
# docker-compose.prod.yml  (example — create this file yourself)
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ctfdb
      POSTGRES_USER: ctf_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  web:
    build: .
    ports:
      - "5000:5000"
    depends_on: [db, redis]
    environment:
      DATABASE_URL: postgresql://ctf_user:${DB_PASSWORD}@db:5432/ctfdb
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
      FLASK_ENV: production
      SESSION_COOKIE_SECURE: "True"
    volumes:
      - uploads:/app/uploads

volumes:
  pgdata:
  uploads:
```

```bash
docker compose -f docker-compose.prod.yml up -d
# Apply migrations
docker compose -f docker-compose.prod.yml exec web flask db upgrade
```

---

## Production Deployment (Gunicorn + Nginx)

### Gunicorn

```bash
gunicorn wsgi:application \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --worker-class gthread \
  --threads 2 \
  --timeout 60 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

**Workers formula:** `(2 × CPU cores) + 1`

### Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name ctf.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name ctf.example.com;

    ssl_certificate     /etc/letsencrypt/live/ctf.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ctf.example.com/privkey.pem;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/static/;
        expires 7d;
    }
}
```

Set `TRUSTED_PROXIES=1` in `.env` when behind Nginx.

---

## Cloud Deployment (Render.com)

A `render.yaml` is included for zero-config deployment:

1. Fork the repository on GitHub.
2. Go to [Render.com](https://render.com) → **New Web Service** → select your fork.
3. Render auto-detects `render.yaml`.
4. Add the following **environment variables** in the Render dashboard:
   - `SECRET_KEY`
   - `ADMIN_PASSWORD`
   - `DATABASE_URL` *(use a Render Postgres add-on)*
5. Deploy!

---

## Security Checklist

Before going live, confirm all of the following:

- [ ] `SECRET_KEY` is a randomly generated 32+ character string (`python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] `ADMIN_PASSWORD` is changed from the default
- [ ] `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] `FLASK_ENV=production` (disables debug mode and traceback pages)
- [ ] `TRUSTED_PROXIES` matches the number of proxy hops in your stack
- [ ] `ALLOWED_HOSTS` is set to your actual domain(s)
- [ ] TLS certificate is installed and HTTP→HTTPS redirect is configured
- [ ] Uploaded file storage is outside the web root (served via redirect, not directly)
- [ ] Log rotation is configured for `logs/`
- [ ] Database backups are scheduled
