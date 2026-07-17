# Deployment Rollback Checklist
# CTF Arena v1.0.0 — EthicBids Technologies™

In the event of a deployment failure, runtime crash, or database corruption during a production update, execute the following rollback procedures to restore the platform to a known good state.

---

## 1. Rollback Criteria

Initiate a rollback immediately if:
1. The app container fails to boot or loops in `restarting` state.
2. The production health check script fails with one or more HTTP 500 errors.
3. Severe latency or database deadlocks are detected during the post-launch walkthrough.
4. Security auditing reveals a breach or access control leakage.

---

## 2. Rollback Steps (Standard Stack)

### Step A: Stop the Active Failed Stack
```bash
docker compose -f deployment/docker-compose.production.yml stop
```

### Step B: Revert the Image Version Tag
1. Open `.env.production` in your deployment directory.
2. Revert the `APP_VERSION` tag back to the previous stable release version (e.g., from `1.0.0` to `0.9.9`, or to a verified SHA).
3. If necessary, pull the previous stable image:
   ```bash
   docker pull ghcr.io/your-org/ctf-arena:<previous_stable_tag>
   ```

### Step C: Database Restoration (State Reset)
If the database schema was modified or data became corrupted during the update:
1. Re-provision the database container clean or clear current tables.
2. Execute the restore script with the last verified daily backup archive:
   ```bash
   ./scripts/restore.sh --backup-dir /opt/ctf-arena/backups/YYYYMMDD_HHMMSS
   ```

### Step D: Restart the Stack
Restart the services with the stable configuration parameters:
```bash
docker compose -f deployment/docker-compose.production.yml up -d --force-recreate
```

---

## 3. Verification Post-Rollback

- [ ] Confirm all container states are `Up` and healthy.
- [ ] Run the health check suite: `python scripts/production_healthcheck.py`.
- [ ] Verify database connectivity and schema integrity by checking migration status:
  ```bash
  docker exec ctf-arena-app flask db current
  ```
- [ ] Verify that logs (`logs/error.log`) are free of unhandled python tracebacks.
