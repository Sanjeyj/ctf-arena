# Known Issues & Workarounds
# CTF Arena v1.0.0 — EthicBids Technologies™

This document lists known bugs, operational limitations, or configuration warnings for CTF Arena v1.0.0.

---

## 1. Application Issues

### Issue A: DeprecationWarning for `utcnow()` in python 3.12+
* **Symptom**: Pytest logs multiple deprecation warnings:
  `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal...`
* **Impact**: Visual warning output in CLI. No runtime impact.
* **Workaround**: The codebase continues to compile and run successfully. Future versions will update references to timezone-aware UTC objects.

### Issue B: SQLAlchemy 2.0 LegacyAPIWarning
* **Symptom**: Warning logs when retrieving model instances:
  `LegacyAPIWarning: The Query.get() method is considered legacy...`
* **Impact**: Warning logging only.
* **Workaround**: No action required; the legacy `.get()` query wrapper remains supported.

---

## 2. Docker / Deployment Issues

### Issue C: Docker Daemon Unreachable Warning
* **Symptom**: App container logs warn:
  `Docker daemon unreachable - running in SIMULATION mode.`
* **Impact**: Dynamic challenge containers cannot be spawned in staging/local environments that do not map `/var/run/docker.sock`.
* **Workaround**:
  - In production, map the host docker socket to the app container.
  - In offline or simulation testing environments, this warning is expected and the platform automatically falls back to simulation mode for challenge verification.

### Issue D: Rate Limiting Falls Back to In-Memory
* **Symptom**: Warning in logs regarding rate limit storage fallback.
* **Impact**: Rate limiting is not synchronized across multiple Gunicorn workers.
* **Workaround**: Ensure `REDIS_URL` is set and valid in `.env.production` to force the app to route rate-limiting keys through Redis.
