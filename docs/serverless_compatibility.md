# Serverless Compatibility Analysis
# CTF Arena v1.0.0 — EthicBids Technologies™

This document analyzes the execution behaviors of the CTF Arena v1.0.0 Flask application in a serverless context (such as Vercel Functions).

---

## 1. Stateless Execution Constraints

Serverless environments spin up ephemeral containers that handle single requests and terminate. To execute successfully on Vercel, the platform conforms to the following guidelines:

### A. Local Filesystem Constraints
* **Restriction**: Vercel Serverless Functions execute on a **read-only filesystem**. Files cannot be written directly to `static/` or the root workspace at runtime.
* **Resolution**: 
  - All file uploads are stored in memory or written temporarily to `/tmp` (the only writeable path inside serverless sandboxes).
  - Production deployments use external cloud storage (like AWS S3) for challenge files, or reference static challenge files packaged with the build.
  - The SQLite database path (`instance/ctf.db`) is replaced with an external PostgreSQL server connection.

### B. Session and Cache States
- Sessions are cryptographically signed and stored entirely client-side using Flask's secure session cookies. No server-side session lookup is required.
- Rate-limiting uses an external Redis database (`REDIS_URL`) instead of local in-memory storage, ensuring rate-limit pools sync across dynamic lambda instances.

### C. Absolute Paths Resolution
- Path references use `os.path.dirname(os.path.abspath(__file__))` to dynamically compute path contexts rather than hardcoded local system directories.
