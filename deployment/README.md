# CTF Arena v2 — Deployment Guide

## Quick Start (Docker Compose)

```bash
# 1. Clone / copy deployment directory
cd /opt && git clone <repo-url> ctf-arena && cd ctf-arena

# 2. Set required environment variables
cp .env.example .env
# Edit .env and set: SECRET_KEY, DATABASE_URL, etc.

# 3. Build & start all services
cd deployment
docker-compose up -d --build

# 4. Initialize database
docker-compose exec app flask init-db
docker-compose exec app flask seed
```

Access:
- App:       https://YOUR_DOMAIN/
- Prometheus: http://localhost:9090
- Grafana:   http://localhost:3000 (admin / ctf_grafana_2024)

---

## Systemd (Without Docker)

```bash
# 1. Create system user
sudo useradd -r -s /bin/false -d /opt/ctf-arena ctfarena
sudo mkdir -p /opt/ctf-arena && sudo chown ctfarena: /opt/ctf-arena

# 2. Deploy code
sudo -u ctfarena git clone <repo-url> /opt/ctf-arena
cd /opt/ctf-arena && sudo -u ctfarena python3 -m venv venv
sudo -u ctfarena venv/bin/pip install -r requirements.txt

# 3. Install services
sudo cp deployment/systemd/ctf-arena.service /etc/systemd/system/
sudo cp deployment/systemd/ctf-arena-janitor.service /etc/systemd/system/
sudo cp deployment/systemd/ctf-arena-janitor.timer /etc/systemd/system/

# 4. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now ctf-arena
sudo systemctl enable --now ctf-arena-janitor.timer

# 5. Install Nginx config
sudo cp deployment/nginx.conf /etc/nginx/sites-available/ctf-arena
sudo ln -s /etc/nginx/sites-available/ctf-arena /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| SECRET_KEY | YES | (none) | Flask secret key |
| DATABASE_URL | No | sqlite:///instance/ctf.db | SQLAlchemy DB URI |
| TRUSTED_PROXIES | No | 0 | Number of reverse proxy hops |
| SESSION_COOKIE_SECURE | No | False | Enforce HTTPS cookies |
| METRICS_ENABLED | No | True | Enable /metrics endpoint |
| RATE_LIMIT_LOGIN | No | 5 per minute | Login attempt limit |
| RATE_LIMIT_SUBMIT | No | 10 per minute | Flag submission limit |
| RATE_LIMIT_API | No | 60 per minute | API request limit |
| GUNICORN_WORKERS | No | cpu*2+1 | Gunicorn worker count |
| GUNICORN_TIMEOUT | No | 30 | Worker timeout |

---

## Health Endpoints

| Endpoint | Purpose |
|---|---|
| GET /live | Liveness probe |
| GET /ready | Readiness probe (DB + filesystem) |
| GET /health | Full system health JSON |
| GET /metrics | Prometheus text metrics |

---

## Backup & Restore

```bash
flask backup-db                          # SQLite hot-backup to instance/backups/
flask backup-db --file /tmp/manual.db   # Custom path
flask restore-db /tmp/manual.db --force # Force restore (no confirmation prompt)
flask snapshot-system                   # Full ZIP archive (DB + uploads)
flask verify-config                     # Pre-flight config sanity checks
```

---

## Log Management

```bash
flask rotate-logs           # Force rotation of all log handlers
flask cleanup-logs          # Remove archived logs older than 30 days
flask cleanup-logs --days 7 # Custom age threshold
```

Logs are stored in:
- `logs/app.log` — Application events
- `logs/access.log` — HTTP requests
- `logs/audit.log` — Security/authentication events  
- `logs/error.log` — Errors and exceptions
- `logs/container.log` — Docker container events
