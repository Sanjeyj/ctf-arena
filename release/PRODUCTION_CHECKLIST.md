# Production Readiness Checklist
# CTF Arena v1.0.0 — EthicBids Technologies™

Use this checklist to verify that all system dependencies, configuration settings, and security audits are complete before starting a production deployment.

---

## Phase A: Pre-Flight Verification

- [ ] **Code Freeze Audit**: Confirm no development files or testing mocks are active.
- [ ] **Tests Execution**: Run full test suite (`python -m pytest`) and verify **1609/1609 PASS**.
- [ ] **DOM Certification**: Verify DOM assertion suite is complete with **236/236 PASS**.
- [ ] **Secrets Initialization**:
  - [ ] Generate secure 64-character hex `SECRET_KEY`.
  - [ ] Set complex passwords for DB, Redis, and Grafana.
  - [ ] Verify that default development passwords are not used anywhere.

---

## Phase B: Infrastructure Validation

- [ ] **Docker Engine**: Check that Docker and Compose versions meet minimum specifications.
- [ ] **Host Ports**: Ensure ports 80 and 443 are open, and ports 5432 / 6379 / 9090 are blocked from public routing.
- [ ] **Reverse Proxy Configurations**:
  - [ ] Place valid SSL certificates inside `deployment/certs/`.
  - [ ] Verify Nginx syntax configuration: `nginx -t` inside proxy container.
  - [ ] Enforce HTTPS redirection and HSTS headers.

---

## Phase C: Application Startup

- [ ] **Stack Boot**: Spin up the containers using `docker compose -f deployment/docker-compose.production.yml up -d`.
- [ ] **Database Setup**: Run `flask db upgrade` to ensure schema is at the migration head (`8bce79803ffc`).
- [ ] **Roles & Admin Seeding**: Run `flask seed` to build initial RBAC structures.
- [ ] **User Verification**: Change default admin password immediately on the first login to the panel.
- [ ] **Metrics Scraper**: Verify Prometheus is scraping `/metrics` and target status is `UP`.

---

## Phase D: Post-Launch Walkthrough

- [ ] Run the automated health test script: `python scripts/production_healthcheck.py`.
- [ ] Verify user registration and session persistence works.
- [ ] Submit a flag to verify database write operations and scoring engine function.
- [ ] Check logs folder (`logs/error.log`) to confirm zero unhandled Python exceptions exist.
