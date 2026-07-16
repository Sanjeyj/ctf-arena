# Platform Architecture Reference — Cyber Defense Platform

## 1. System Topology

The Cyber Defense Platform is designed around a three-tier local architecture:

```
[Web UI (Vanilla HTML/CSS)] <── HTTP ──> [Flask Application Layer]
                                           │
                                     SQLAlchemy ORM
                                           │
                                           ▼
                                    [SQLite Database]
```

- **Frontend Tier**: Serves modernized responsive templates using Vanilla CSS (`ui-modernization.css`) and responsive interaction handlers (`ui-shell.js`).
- **Application Tier**: A modular Flask app structured around phase blueprints, services, and middleware extensions.
- **Database Tier**: Relies on a local SQLite instance managed with SQLAlchemy and Alembic migrations.

---

## 2. Core Concepts & Decoupling

- **Application Factory (`app/create_app()`)**: Creates isolated app instances, attaches extensions, registers blueprints dynamically, and registers context processors.
- **Service Domain Layer**: Business logic is separated from routes. Services handle database lookups, simulation state calculations, and data mutation tasks.
- **Event Orchestration (Hook Registry)**: Modules communicate asynchronously using the hook engine (`app/services/hook_service.py`) to prevent direct package coupling.
- **Security Boundaries**: JWT verify helpers enforce token context, and SQLAlchemy session contexts restrict queries to the caller's `organization_id`.
