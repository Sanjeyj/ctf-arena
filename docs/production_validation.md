# Production Validation Specification
# CTF Arena v1.0.0 — EthicBids Technologies™

## Overview

This specification details the post-deployment validation plan for CTF Arena v1.0.0 to verify that the application has been successfully configured and is operating normally in a production environment.

---

## 1. Post-Deployment Verification Checklist

Once the production deployment pipeline completes successfully, execute these validation steps.

### Step 1: Core Process Verification
- Verify that the three main containers are running with correct restart policies:
  ```bash
  docker compose -f deployment/docker-compose.production.yml ps
  ```
  Expected output should show:
  * `ctf-arena-app` — `Up (healthy)`
  * `ctf-arena-nginx` — `Up`
  * `ctf-arena-db` — `Up (healthy)`
  * `ctf-arena-redis` — `Up (healthy)`

- Verify non-root execution inside the app container:
  ```bash
  docker exec ctf-arena-app whoami
  ```
  Expected output: `1001` or `ctfarena` (must not be `root`).

### Step 2: Automated Health Verification
Run the production healthcheck script to verify 20+ core routes and confirm no HTTP 500 errors:
```bash
python scripts/production_healthcheck.py --base-url https://your-domain.com
```
Expected output: `✅ PRODUCTION HEALTH CHECK PASSED`.

---

## 2. Dynamic Functional Walkthrough

To verify security isolation, RBAC mapping, and the operational engine, perform the following validation actions:

### Scenario A: Participant Sign-up & Authentication
1. Navigate to `https://your-domain.com/register`.
2. Create a test participant account with:
   - Username: `TestUser123`
   - Email: `testuser@your-domain.com`
   - Password: `Password@1234`
3. Verify registration redirects to the dashboard home.
4. Log out, then log back in using the credentials to verify session persistence.

### Scenario B: Dynamic Challenge Interaction
1. Log in as `TestUser123`.
2. Click on the **Challenges** page.
3. Access a challenge from the available list.
4. Submit a dummy flag (e.g., `flag{wrong_flag_test}`).
5. Confirm that the page displays "Incorrect Flag" (validates scoring service boundary).
6. Verify no runtime errors are logged in the console.

### Scenario C: Administrator Control & Auditing
1. Log in to the Admin Panel at `https://your-domain.com/admin/login` using seeded admin credentials.
2. Verify access to:
   - **User Ledger**: Verify participant `TestUser123` is registered.
   - **Submissions Logs**: Verify the failed flag submission is recorded.
   - **Announcements**: Broadcast a test announcement to verify live messaging.

---

## 3. Incident Logging & Rollback Condition

If any validation check fails:
1. Immediately execute the **Rollback Checklist** (defined in `release/ROLLBACK_CHECKLIST.md`).
2. Log the failure reason in `/opt/ctf-arena/logs/deploy_failures.log` with the current timestamp.
