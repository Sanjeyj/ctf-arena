# Security Hardening & Operator Guide — Cyber Defense Platform

This manual details the security boundaries, access controls, and AI security configuration instructions.

---

## 1. Authentication & API Authorization

- **JWT Tokens**: Ensure that `JWT_SECRET_KEY` in the environment configuration (`.env`) is set to a long, cryptographically secure random string before starting production servers.
- **Session Security**: Session cookies default to `HttpOnly` and `SameSite=Lax`. In production environments with HTTPS enabled, configure `SESSION_COOKIE_SECURE=True` in `config.py`.
- **Role-Based Access**: Role scopes (Participant vs. Administrator) are evaluated at the blueprint and view decorator levels. Administrator actions are restricted to registered admin accounts.

---

## 2. Inbound Input Filtering

- **Input Validation**: All requests are schema-checked by Marshmallow schemas or WTForms validators.
- **CSRF Token Integrity**: Form templates include `{{ form.csrf_token }}` or custom security headers for all state-changing API requests.

---

## 3. Platform AI Hardening

- **Prompt Injection Filter Rules**: Real-time scanners inspect user input for system command patterns and prompt overrides. If triggered, the request is rejected with a validation warning.
- **Information Masking Filters**: Output strings are parsed to mask secrets, API keys, and CTF flags (`CTF{...}`) before display.
- **Simulation Isolation**: The AI module has no network egress capability and operates strictly in offline/local simulation mode.
