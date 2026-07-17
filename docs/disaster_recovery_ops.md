# Disaster Recovery Operations Runbook
# CTF Arena v1.0.0 — EthicBids Technologies™

> [!IMPORTANT]
> This is the **Operational** disaster recovery runbook for platform operators.
> It covers backup procedures, RPO/RTO targets, and step-by-step recovery actions.

---

## Recovery Objectives

| Metric | Target |
|--------|--------|
| **RPO** (Recovery Point Objective) | 24 hours (daily backup cycle) |
| **RTO** (Recovery Time Objective) | 2 hours (single-node restore) |
| Backup frequency | Daily at 02:00 UTC |
| Backup retention | 30 days local, 90 days S3 |
| Backup test frequency | Monthly |

---

## Backup Schedule

```bash
# Add to crontab (crontab -e)
# Daily database + uploads backup at 02:00 UTC
0 2 * * * /opt/ctf-arena/scripts/backup.sh >> /opt/ctf-arena/logs/backup.log 2>&1

# Weekly config backup on Sundays at 03:00 UTC
0 3 * * 0 /opt/ctf-arena/scripts/backup.sh --db-only >> /opt/ctf-arena/logs/backup.log 2>&1
```

---

## Scenario 1: Application Crash / Unresponsive

**Symptoms**: HTTP 502 from Nginx, health check failing, no response.

**RTO Target**: 5 minutes

```bash
# 1. Check container status
docker compose -f deployment/docker-compose.production.yml ps

# 2. View recent logs
docker compose -f deployment/docker-compose.production.yml logs --tail=100 app

# 3. Restart application container
docker compose -f deployment/docker-compose.production.yml restart app

# 4. Verify health
curl -s http://localhost:8000/health
```

---

## Scenario 2: Database Corruption / Loss

**Symptoms**: SQLAlchemy errors, database query failures, `pg_up == 0`.

**RTO Target**: 2 hours

```bash
# 1. Identify latest backup
ls -lt /opt/ctf-arena/backups/ | head -5

# 2. Dry run to validate backup
./scripts/restore.sh --backup-dir /opt/ctf-arena/backups/YYYYMMDD_HHMMSS --dry-run

# 3. Stop the application
docker compose -f deployment/docker-compose.production.yml stop app

# 4. Execute restore
./scripts/restore.sh --backup-dir /opt/ctf-arena/backups/YYYYMMDD_HHMMSS

# 5. Restart application
docker compose -f deployment/docker-compose.production.yml start app

# 6. Verify
curl -s http://localhost:8000/health
./venv/bin/python scripts/final_dom_certification.py
```

---

## Scenario 3: Full Server Loss

**Symptoms**: Complete host failure, no SSH access.

**RTO Target**: 4 hours (new server provisioning + restore)

```bash
# On a new server:

# 1. Install Docker + Docker Compose
apt update && apt install -y docker.io docker-compose-plugin

# 2. Clone repository
git clone https://github.com/your-org/ctf-arena.git /opt/ctf-arena
cd /opt/ctf-arena

# 3. Restore backup from S3
aws s3 sync s3://your-bucket/ctf-arena/YYYYMMDD_HHMMSS/ /opt/ctf-arena/backups/restore/

# 4. Configure environment
cp .env.production.example .env.production
# Edit .env.production with production credentials

# 5. Start stack
docker compose -f deployment/docker-compose.production.yml --env-file .env.production up -d

# 6. Wait for DB to be healthy, then restore
./scripts/restore.sh --backup-dir /opt/ctf-arena/backups/restore/

# 7. Seed initial data
docker exec ctf-arena-app flask seed

# 8. Verify
curl -s http://localhost/health
```

---

## Scenario 4: Container Image Corruption

**Symptoms**: App container fails to start, image build error.

```bash
# Rollback to previous image tag
docker compose -f deployment/docker-compose.production.yml \
  pull ctf-arena:1.0.0

docker compose -f deployment/docker-compose.production.yml \
  up -d --force-recreate app
```

---

## Scenario 5: Disk Space Exhaustion

**Symptoms**: Nginx returning 500, writes failing, `node_filesystem_avail_bytes` alert.

```bash
# 1. Identify large files
du -sh /opt/ctf-arena/logs/* | sort -h | tail -20
du -sh /opt/ctf-arena/uploads/* | sort -h | tail -20

# 2. Rotate logs
find /opt/ctf-arena/logs -name "*.log" -mtime +7 -exec gzip {} \;
find /opt/ctf-arena/logs -name "*.gz" -mtime +30 -delete

# 3. Clean Docker images
docker image prune -f

# 4. Clean old backups
find /opt/ctf-arena/backups -mtime +30 -type d -exec rm -rf {} +
```

---

## Backup Verification Procedure

Run monthly to validate backup integrity:

```bash
# 1. List latest backup
LATEST=$(ls -td /opt/ctf-arena/backups/*/ | head -1)
echo "Testing backup: ${LATEST}"

# 2. Dry-run restore
./scripts/restore.sh --backup-dir "${LATEST}" --dry-run

# 3. Test database dump integrity
DB_FILE=$(find "${LATEST}" -name "*.sql.gz" | head -1)
gunzip -t "${DB_FILE}" && echo "Database backup: VALID" || echo "Database backup: CORRUPT"

# 4. Verify uploads archive
UPLOADS_FILE=$(find "${LATEST}" -name "uploads_*.tar.gz" | head -1)
tar -tzf "${UPLOADS_FILE}" > /dev/null && echo "Uploads backup: VALID" || echo "Uploads backup: CORRUPT"

# 5. Log result
echo "[$(date)] Backup test: PASSED for ${LATEST}" >> /opt/ctf-arena/logs/backup_tests.log
```

---

## Post-Incident Checklist

After any recovery action:

- [ ] Application health check returns 200
- [ ] Admin login functional
- [ ] Participant login functional
- [ ] Scoreboard loading
- [ ] Challenge pages accessible
- [ ] Flag submission functional
- [ ] Prometheus scraping metrics
- [ ] No error alerts in Grafana
- [ ] Incident documented in ops log
- [ ] Root cause identified and remediated
- [ ] Backup schedule re-verified
- [ ] Stakeholders notified
