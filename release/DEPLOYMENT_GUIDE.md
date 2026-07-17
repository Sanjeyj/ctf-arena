# Production Deployment Guide
# CTF Arena v1.0.0 — EthicBids Technologies™

This guide details the steps to deploy the release-certified CTF Arena v1.0.0 in a hardened production environment using Docker Compose.

---

## 1. Prerequisites

Before starting, ensure the host machine meets the following requirements:

| Component | Minimum Version | Recommendation |
|-----------|-----------------|----------------|
| **OS** | Linux (Ubuntu 22.04+ LTS) | Ubuntu 22.04 LTS |
| **CPU** | 2 Cores | 4 Cores |
| **RAM** | 2 GB | 4 GB+ |
| **Disk** | 20 GB SSD | 50 GB+ SSD |
| **Docker** | 24.0.0+ | Docker Engine 26.0+ |
| **Compose** | v2.20.0+ | Compose v2.26+ |

Network Access:
- Inbound: Ports `80` (HTTP) and `443` (HTTPS)
- Outbound: Registry pull, package updates, SMTP, S3 sync

---

## 2. Infrastructure Architecture

The production stack runs isolated containerized services connected via two internal Docker networks:

```
[ Internet ] 
     │ (Ports 80, 443)
     ▼
[ Nginx Container (Reverse Proxy) ]
     │ (Frontend Bridge Net)
     ▼
[ Flask App Container (Gunicorn) ] ── (Backend Internal Net) ──► [ PostgreSQL ]
                                                                 ► [ Redis ]
                                                                 ► [ Prometheus ]
                                                                 ► [ Grafana ]
```

- **Frontend Network**: Allows Nginx to proxy traffic to Gunicorn.
- **Backend Network**: Internal bridge network with no external ports exposed. Isolates database, cache, and metrics scrapers.

---

## 3. Deployment Steps

### Step A: Clone & Directory Setup
Clone the frozen release package to the target directory:
```bash
git clone https://github.com/your-org/ctf-arena.git /opt/ctf-arena
cd /opt/ctf-arena
```

### Step B: Environment Configuration
Copy the production environment template and generate secure keys:
```bash
cp .env.production.example .env.production
```
Edit `.env.production` and configure the following variables:
- `SECRET_KEY`: Random 64 hex characters (`python -c "import secrets; print(secrets.token_hex(64))"`)
- `ADMIN_PASSWORD`: Strong password for the seeded administrator account.
- `POSTGRES_PASSWORD`: Strong password for PostgreSQL backend credentials.
- `REDIS_PASSWORD`: Strong password for Redis authentication.
- `GRAFANA_PASSWORD`: Strong password for Grafana administrative access.
- `DOMAIN`: Public target domain name.

### Step C: SSL Certificates
For Nginx to boot correctly, TLS certificates must be placed in `deployment/certs/`.
If using Let's Encrypt / Certbot:
```bash
# Obtain certificates via certbot standalone
certbot certonly --standalone -d your-domain.com

# Link them into the certs folder
mkdir -p deployment/certs
ln -sf /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/certs/fullchain.pem
ln -sf /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/certs/privkey.pem
```

### Step D: Build & Start Stack
Run the docker compose command with the production configuration:
```bash
docker compose -f deployment/docker-compose.production.yml --env-file .env.production up -d --build
```

### Step E: Database Migrations & Seeding
Once the PostgreSQL container is healthy, run database migrations and seed the initial roles and users:
```bash
# Upgrade schema to migration head
docker exec ctf-arena-app flask db upgrade

# Seed roles, permissions, and seeded default accounts
docker exec ctf-arena-app flask seed
```

---

## 4. Verification

Verify that all services are online:
```bash
docker compose -f deployment/docker-compose.production.yml ps
```
Run the automated post-deployment health check:
```bash
docker exec ctf-arena-app python scripts/production_healthcheck.py --base-url http://localhost:8000
```
If the check fails, immediately stop the container and execute the rollback procedures.
