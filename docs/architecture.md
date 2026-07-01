# CTF Arena v2 — Architecture Overview

This document describes the application architecture, component responsibilities,
data flow, and key design decisions in CTF Arena v2.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Directory Structure](#directory-structure)
3. [Layered Design](#layered-design)
   - [Models](#models)
   - [Repositories](#repositories)
   - [Services](#services)
   - [Blueprints (Routes)](#blueprints-routes)
4. [Shared Extensions](#shared-extensions)
5. [Request Lifecycle](#request-lifecycle)
6. [Key Design Decisions](#key-design-decisions)
7. [Database Schema (ERD summary)](#database-schema-erd-summary)
8. [Performance Optimisations](#performance-optimisations)
9. [Background Tasks and Scheduling](#background-tasks-and-scheduling)
10. [Plugin System](#plugin-system)

---

## High-Level Architecture

```
Browser / API Client
        │
        ▼
   Nginx (TLS proxy)  ─── optional
        │
        ▼
  Gunicorn / Flask Dev Server
        │
        ├── Static files (/static/)
        │
        └── Flask Application (app/)
              ├── Blueprints (routes)  ──►  Services  ──►  Repositories  ──►  DB (SQLAlchemy)
              ├── Templates (Jinja2)
              ├── Extensions (db, login, csrf, …)
              └── CLI commands (flask <cmd>)
```

---

## Directory Structure

```
ctf-arena/
├── app/
│   ├── __init__.py             # Application factory (create_app)
│   ├── config.py               # Config classes (Dev/Test/Staging/Prod)
│   ├── extensions.py           # Shared extension instances + helpers
│   ├── context_processors.py   # Jinja2 template globals
│   ├── cli.py                  # Flask CLI commands (seed, reset, etc.)
│   │
│   ├── models/                 # SQLAlchemy model definitions
│   ├── repositories/           # DB query layer (CRUD helpers)
│   ├── services/               # Business logic (pure Python)
│   │
│   ├── admin/                  # Admin blueprint
│   ├── analytics/              # Analytics blueprint
│   ├── announcements/          # Announcements blueprint
│   ├── api/                    # JSON API v1 blueprint
│   ├── audit/                  # Audit-log blueprint
│   ├── auth/                   # Auth blueprint (login / register)
│   ├── categories/             # Category management blueprint
│   ├── certificates/           # Certificate generation blueprint
│   ├── challenges/             # Challenge pages blueprint
│   ├── competitions/           # Competition management blueprint
│   ├── docker/                 # Container challenge management blueprint
│   ├── files/                  # File upload / download blueprint
│   ├── flags/                  # Flag management blueprint
│   ├── hints/                  # Hint management blueprint
│   ├── middleware/             # WSGI middleware (proxy, host check)
│   ├── notifications/          # Push notification blueprint
│   ├── plugins/                # Plugin loading infrastructure
│   ├── scheduler/              # APScheduler background jobs
│   ├── scoreboard/             # Live scoreboard blueprint
│   ├── submissions/            # Submission blueprint
│   ├── teams/                  # Team management blueprint
│   ├── themes/                 # Theme-switching blueprint
│   ├── users/                  # User profile blueprint
│   └── utils/                  # Shared utility functions
│
├── docs/                       # This documentation
├── migrations/                 # Alembic migration scripts
├── plugins/                    # External plugin directory
├── static/                     # Static assets (CSS, JS, images)
├── templates/                  # Jinja2 HTML templates
├── tests/                      # pytest test suite
├── uploads/                    # User-uploaded challenge files
├── instance/                   # Runtime data (DB, logs) — gitignored
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py                      # Dev server entry point
└── wsgi.py                     # Gunicorn entry point
```

---

## Layered Design

The application follows a strict three-layer separation:

```
Routes (Blueprint)
    │  receives HTTP request, validates input, calls service
    ▼
Service
    │  business logic, composes repository calls, raises exceptions
    ▼
Repository
    │  raw DB queries; returns model instances
    ▼
Model (SQLAlchemy)
```

### Models

Located in `app/models/`. Each file defines one SQLAlchemy model.

| Model | Table | Purpose |
|-------|-------|---------|
| `User` | `user` | Participant account |
| `Team` | `team` | Optional grouping of users |
| `Challenge` | `challenge` | CTF challenge definition |
| `Flag` | `flag` | Correct answer(s) for a challenge |
| `Submission` | `submission` | Flag attempt record |
| `Category` | `category` | Challenge category |
| `Hint` | `hint` | Optional paid hints |
| `HintUnlock` | `hint_unlock` | Records which user unlocked which hint |
| `Competition` | `competition` | Time-bounded competition event |
| `Announcement` | `announcement` | Admin broadcast messages |
| `DockerImage` | `docker_image` | Registered Docker images for container challenges |
| `DeploymentProfile` | `deployment_profile` | Named Docker deployment configuration |
| `ChallengeInstance` | `challenge_instance` | Running container for a user/challenge |
| `ContainerLog` | `container_log` | Container lifecycle events |
| `InstanceSnapshot` | `instance_snapshot` | Checkpoint state of a running container |
| `LoginHistory` | `login_history` | Authentication event log |

**`TimestampMixin`** (`app/models/mixins.py`) automatically adds `created_at` and
`updated_at` columns to any model that inherits it.

### Repositories

Located in `app/repositories/`. Each repository wraps queries for one model.

```python
# Pattern example
class ChallengeRepository:
    @staticmethod
    def get_all_visible():
        return Challenge.query.filter_by(visible=True).options(
            joinedload(Challenge.category)
        ).order_by(Challenge.created_at).all()
```

All write operations use `safe_commit()` from `app/extensions.py` to ensure
DB errors are caught and the session is rolled back cleanly:

```python
def safe_commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
```

### Services

Located in `app/services/`. Services contain pure business logic and may compose
multiple repository calls into a single transaction-safe operation.

| Service | Responsibility |
|---------|---------------|
| `SessionService` | Login validation, password hashing, session management |
| `ChallengeService` | Challenge listing, flag verification, elapsed-time scoring |
| `LiveScoreboardService` | Real-time score snapshot + freeze logic |
| `CompetitionService` | Active competition lookup + state machine |
| `AnnouncementService` | Scheduled announcement filtering |
| `InstanceService` | Container lifecycle (start, stop, prune) |
| `MetricsService` | Platform-wide statistics aggregation |
| `DockerService` | Low-level Docker SDK interactions |

### Blueprints (Routes)

Each Blueprint is registered in `app/__init__.py` via `create_app()`. Blueprints
are thin: they validate input, call a service or repository, and render a
template or return JSON.

---

## Shared Extensions

`app/extensions.py` holds all Flask extension singletons and shared helpers:

```python
db          # Flask-SQLAlchemy
login_manager  # Flask-Login
csrf        # Flask-WTF CSRF protection

def safe_commit():   # Wraps db.session.commit() with rollback on failure
def utcnow():        # timezone-naive UTC datetime (replaces deprecated utcnow())
```

---

## Request Lifecycle

```
1. Incoming HTTP request hits Nginx (or dev server).
2. Gunicorn worker picks up the request.
3. Flask WSGI middleware runs (proxy headers, allowed-hosts check).
4. Flask routes to the matching Blueprint view function.
5. Flask-Login checks session / @login_required decorator.
6. Flask-WTF validates CSRF token on POST requests.
7. Blueprint calls Service or Repository.
8. Repository queries SQLAlchemy ORM.
9. SQLAlchemy generates SQL and queries the database.
10. Result flows back through Service → Blueprint.
11. Blueprint renders Jinja2 template OR returns JSON.
12. Flask-WTF / session middleware finalises response headers.
13. Response is sent back via Gunicorn → Nginx → client.
```

On any unhandled exception after step 8, the teardown handler in
`app/__init__.py` calls `db.session.rollback()` to prevent partial writes.

---

## Key Design Decisions

### Repository Pattern
The repository pattern decouples business logic from the ORM, making it easy
to unit-test services with mock repositories and to swap the data backend
without touching service code.

### `safe_commit()` for All Writes
Every repository write operation uses `safe_commit()` instead of calling
`db.session.commit()` directly. This guarantees clean rollbacks and prevents
connection pool poisoning on DB errors.

### `utcnow()` Helper
Python 3.12+ deprecates `datetime.datetime.utcnow()`. The `utcnow()` helper
returns `datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)`,
which is timezone-naive and compatible with existing SQLite columns while
avoiding deprecation warnings.

### Eager Loading (N+1 Prevention)
Critical list queries (challenge dashboard, scoreboard) use SQLAlchemy
`joinedload()` to fetch related records in a single SQL `JOIN` rather than
issuing one query per object.

### CSRF Protection
All state-changing form submissions are protected by Flask-WTF's CSRF token.
The token is injected globally via the `context_processors.py` Jinja2 context.

### Rate Limiting
Login, flag-submission, and API endpoints are rate-limited via the
`RATE_LIMIT_*` config keys, implemented in the middleware layer.

---

## Database Schema (ERD summary)

```
User ──< Submission >── Challenge ──< Flag
 │                          │
 │                       Category
 │
 ├──< HintUnlock >── Hint >── Challenge
 ├──< LoginHistory
 ├──< ChallengeInstance >── ContainerLog
 │                     └──< InstanceSnapshot
 └──< Team (via TeamMember join table)

Competition (standalone, referenced by CompetitionService)
Announcement (standalone)
DockerImage ──< DeploymentProfile
```

---

## Performance Optimisations

| Optimisation | Location | Impact |
|-------------|----------|--------|
| `joinedload(Challenge.category)` | `ChallengeRepository` | Eliminates N+1 on dashboard |
| `joinedload(Submission.challenge)` | `SubmissionRepository` | Eliminates N+1 on scoreboard |
| `joinedload(HintUnlock.hint)` | `UserRepository` | Eliminates N+1 on profile hints |
| Index on `ChallengeInstance.expires_at` | `challenge_instance.py` model | Speeds up instance pruning queries |
| `db_session.rollback()` teardown | `app/__init__.py` | Prevents connection stalls |

---

## Background Tasks and Scheduling

The `app/scheduler/` package integrates **APScheduler** to run periodic jobs:

| Job | Schedule | Purpose |
|-----|----------|---------|
| Instance pruning | Every 5 min | Terminate expired challenge containers |
| Metrics snapshot | Hourly | Persist platform stats to `ContainerLog` |

---

## Plugin System

The `app/plugins/` package loads extensions from the top-level `plugins/`
directory at application startup. Each plugin must expose a `register(app)`
function:

```python
# plugins/my_plugin/__init__.py
def register(app):
    from flask import Blueprint
    bp = Blueprint("my_plugin", __name__)

    @bp.route("/myplugin")
    def index():
        return "Hello from plugin!"

    app.register_blueprint(bp)
```

Plugins are discovered automatically; no configuration is required.
