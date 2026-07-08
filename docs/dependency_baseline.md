# Dependency & Reproducibility Baseline (v1.0.0)

**Date**: 2026-07-08  
**Status**: ✅ AUDITED

---

## 1. Runtime Dependencies

The platform's runtime depends on the following libraries (as defined in `setup.py` and `requirements.txt`):

| Library Name | Version Specifier | Category | Purpose |
|---|---|---|---|
| **flask** | `>=3.0.0` | Core GRC / MVC | Application framework |
| **pillow** | `>=10.0.0` | Media Processing | Image resizing and validation |
| **gunicorn** | `>=21.2.0` | WSGI Server | Production application server |
| **python-dotenv** | `>=1.0.0` | Configuration | Load environment variables from `.env` |
| **flask-sqlalchemy** | `>=3.1.0` | ORM | Database connectivity and mapping |
| **flask-migrate** | `>=4.0.0` | Migrations | Alembic database migration management |
| **psycopg2-binary** | `>=2.9.9` | Postgres Driver | PostgreSQL backend connectivity |
| **flask-login** | `>=0.6.3` | Authentication | Session user management |
| **bcrypt** | `>=4.1.0` | Security | Password hashing |
| **flask-wtf** | `>=1.2.1` | Security | CSRF and form validation |
| **flask-limiter** | `>=3.5.0` | Security | Rate limiting |
| **docker** | `>=7.0.0` | Orchestration | Interactive challenge container management |

---

## 2. Test & Development Dependencies

- **pytest** (`>=7.4.0`): Core unit and integration test runner.
- No other third-party tooling is required for development or regression runs.

---

## 3. Database & AI Dependencies

- **SQLite**: No external packages. Uses Python's native standard library module `sqlite3`.
- **PostgreSQL**: Supported via `psycopg2-binary`.
- **AI Framework**: The AI briefings and sanitizers are implemented directly using Flask and standard Python structures. The `StubProvider` requires no third-party libraries (e.g., LangChain or OpenAI SDK).

---

## 4. Reproducibility Risks & Mitigations

- **Risk: Version Drift**: The versions in `requirements.txt` and `pyproject.toml` are declared with logical range constraints (e.g., `flask>=3.0.0`). This creates a risk where installation on a new environment could pull newer minor or major versions, resulting in compatibility breakage or deprecation issues.
- **Mitigation Strategy**:
  - Developers should install using `pip install -e .` or pin exact versions in local virtual environments.
  - For production setups, a locked version requirements file (e.g. standard output of `pip freeze`) should be maintained to guarantee identical package versions.
  - Python version is constrained to `>=3.10` in package metadata.
