# Cyber Defense Platform Operations Handbook
**Release Version:** 1.0.0
**Branding:** EthicBids Technologies™

This runbook structures the deployment, maintenance, configuration, and monitoring procedures for platform operators.

---

## 1. Deployment & Infrastructure

### 1.1 Docker Compose Execution
For production deployment, run the compose stack with resource constraints:
```bash
docker-compose -f deployment/docker-compose.production.yml up -d
```

### 1.2 Reverse Proxy Hardening
Ensure Nginx or Caddy enforces HTTPS, HSTS, and CSP headers:
```nginx
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;" always;
```

---

## 2. Maintenance & Caching

### 2.1 Database Backup & Encryption
A backup cron job dumps the database hourly, encrypts using GPG, and rotates files older than 30 days:
```bash
bash scripts/backup.sh --encrypt --rotate
```

### 2.2 System Caching Policy
Static assets under `/static` have their Cache-Control headers set to max longevity (1 year) with fingerprinting (cache busting) configured in template blocks.
```python
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response
```
*(This logic is configured in the frozen server backend; do not modify).*
