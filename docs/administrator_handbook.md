# Cyber Defense Platform Administrator Handbook
**Release Version:** 1.0.0
**Config Standard:** Enterprise Product Excellence v1.0

This guide details configuration settings, environment keys, roles, and administrative variables.

---

## 1. Environment Variable Specifications

Ensure that the following variables are defined in the runtime context (e.g. `.env` or Vercel settings):

| Key | Type | Description | Mandatory |
|---|---|---|---|
| `FLASK_APP` | String | Set to `run.py` to point to app context | YES |
| `SECRET_KEY` | String | High-entropy cryptographic secret for session signing | YES |
| `DATABASE_URL` | String | Database connection endpoint (SQLite, PostgreSQL) | YES |
| `REDIS_URL` | String | Caching server connection string | NO |
| `WTF_CSRF_ENABLED` | Boolean| CSRF validation control flag | YES |

---

## 2. Role-Based Access Controls (RBAC)
- **Administrator (`admin`)**: Access to all panels, live stats reset controls, and plugin activation matrices.
- **Participant (`user`)**: Can download challenges, submit flags, buy hints, and view public scoreboard rankings.
- **Anonymous**: Access restricted to public scoreboard page (`/scoreboard`) and login/register.
