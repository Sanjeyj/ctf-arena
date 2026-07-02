# Release Notes — CTF Arena v1.0.0-rc1

Welcome to the first Release Candidate of **CTF Arena v2**. This release elevates the lightweight, college-targeted CTF platform into a production-grade, containerized, and high-performance competitive engine.

---

## Key Highlights

### 1. Zero-Config Docker Challenges
Host web, pwn, or reversing tasks easily. Each competitor gets an isolated, ephemeral container. Expiry timers, resource ceilings, and dynamic port configurations are handled automatically.

### 2. Time-Naive UTC & Safe Commits
Optimized database integrity with `safe_commit()`, protecting connection pools against broken sessions. Standardized timezone logic using the `utcnow()` helper to prevent date comparison errors.

### 3. High Performance
Dashboard cards and scoreboard statistics fetch in one query via SQLAlchemy eager-loading (`joinedload`), ensuring response times remain below 50 ms under concurrent load.

### 4. Built-in Security Controls
Enforces session security, HTTP-only/secure cookies, CSRF protection, and account lockout constraints by default. Exposes auditing lines in a dedicated viewer.

---

## Quick Setup

```bash
# Clone the repository
git clone https://github.com/Sanjeyj/ctf-arena.git
cd ctf-arena

# Install requirements
pip install -r requirements.txt

# Seed roles, default users, and challenges
flask db upgrade
flask seed

# Run local development server
export FLASK_ENV=development
flask run
```

Access the admin portal at `http://localhost:5000/admin` (Default: `admin` / `ctf_admin_2024`).
