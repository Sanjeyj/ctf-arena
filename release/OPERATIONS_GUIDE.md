# Platform Operations Guide
# CTF Arena v1.0.0 — EthicBids Technologies™

This guide details day-to-day operations, system commands, log inspection, and troubleshooting procedures for CTF Arena v1.0.0.

---

## 1. System Administration Commands

Use the following commands to manage the production container stack.

### Start Stack
```bash
docker compose -f deployment/docker-compose.production.yml --env-file .env.production up -d
```

### Stop Stack
```bash
docker compose -f deployment/docker-compose.production.yml stop
```

### Restart Application Service (safe reload)
```bash
docker compose -f deployment/docker-compose.production.yml restart app
```

### View Service Health Status
```bash
docker compose -f deployment/docker-compose.production.yml ps
```

---

## 2. Inspecting Logs

Logs are segmented by service. Standard log streams:

### Gunicorn Web App Logs
- **Error Log**: `logs/error.log` (monitors Tracebacks, 500 crashes)
- **Access Log**: `logs/access.log` (monitors incoming HTTP request routing)
```bash
# Tail application logs
tail -f logs/error.log
```

### Nginx Access & Error Logs
- Streamed directly to Docker stdout:
```bash
docker compose -f deployment/docker-compose.production.yml logs -f nginx
```

### Database Log Stream
```bash
docker compose -f deployment/docker-compose.production.yml logs -f db
```

---

## 3. Maintenance Tasks

### Clearing App Cache
Redis contains rate-limiting and temporary page caches. To clear the cache without restarting the app:
```bash
docker exec ctf-arena-redis redis-cli -a <REDIS_PASSWORD> flushall
```

### Backup Triggers
Verify that backups are executing successfully according to crontab schedules:
```bash
# Manual backup execution
/opt/ctf-arena/scripts/backup.sh
```

### Database Schema Verifications
Verify that the database schema matches the expected release head (`8bce79803ffc`):
```bash
docker exec ctf-arena-app flask db current
```

---

## 4. Troubleshooting Playbook

### Problem A: HTTP 502 Bad Gateway
* **Possible Cause**: Gunicorn application server is down or rebooting.
* **Remediation**:
  1. Check if the app container is running: `docker ps | grep app`
  2. If exited, review traceback: `tail -n 100 logs/error.log`
  3. Restart app container: `docker compose restart app`

### Problem B: Rate Limiter Blocking Users (HTTP 429)
* **Possible Cause**: Redis connection lost, or legitimate traffic spike.
* **Remediation**:
  1. Check Redis log: `docker compose logs redis`
  2. Test connection from app container to Redis: `docker exec ctf-arena-app nc -zv redis 6379`
  3. Adjust rate limits in `.env.production` if limits are too strict under high load.
