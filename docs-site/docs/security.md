# Security Controls & Hardening

Review the security measures implemented in CTF Arena v2 and deployment recommendations.

---

## 1. Security Mitigations

- **CSRF Enforcement**: Handled via Flask-WTF. CSRF validation is active on all state-changing routes.
- **Session Cookie Flags**: Hardened in production using `HttpOnly=True`, `Secure=True`, and `SameSite=Lax`.
- **Brute-Force & Lockouts**: Limits consecutive failed login attempts to 5 per account. After threshold, accounts are locked and security events are logged.
- **File Upload Safeguards**: Secure filename parsing prevents directory traversal exploit attempts. MIME-type validation rejects unapproved file extensions.

---

## 2. Recommended Hardening

1. **SSL/TLS Configuration**: Ensure Nginx reverse proxy forces TLS 1.2 or 1.3 with HSTS active.
2. **PostgreSQL Credentials**: Run database services under dedicated read/write user roles with restricted permissions.
3. **Docker socket isolation**: Restrict access to the Docker daemon Unix socket (`/var/run/docker.sock`).
