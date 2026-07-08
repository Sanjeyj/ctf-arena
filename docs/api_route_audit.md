# API Route Audit (v1.0.0-rc1)

## Executive Summary

This audit reviews the Flask routing architecture, blueprint registration, endpoint counts, and potential route collisions across all 40 phases of the Cyber Defense Platform (CDP).

---

## Routing Statistics

- **Total Blueprints Registered**: `49`
- **Total Routes (Endpoints)**: `583`
  - **API Endpoints (`/api/`)**: `340`
  - **Admin Endpoints (`/admin/`)**: `202`
  - **Other Endpoints**: `41`

---

## Duplicate Route Findings & Collision Risks

A programmatic scan of the Flask URL map identified **8 endpoint method/path overlaps**. In Flask, when multiple routes share the exact same path and HTTP method, the blueprint registered *first* takes precedence, and subsequent routes are shadowed (inaccessible).

### Collision Details

| Method | Route Path | Shadowed Endpoints | Precedence Order |
|---|---|---|---|
| GET | `/api/v1/hunts` | `soc.list_hunts` <br> `autonomous.list_hunt_sessions` | `soc.list_hunts` takes precedence |
| POST | `/api/v1/hunts` | `soc.create_hunt` <br> `autonomous.create_hunt_session` | `soc.create_hunt` takes precedence |
| GET | `/api/v1/federation` | `ecosystem.list_federations` <br> `intelligence.api_get_federation` | `ecosystem.list_federations` takes precedence |
| GET | `/api/v1/agents` | `autonomous.list_agents` <br> `enterprise.api_get_agents` | `autonomous.list_agents` takes precedence |
| POST | `/api/v1/agents` | `autonomous.create_agent` <br> `enterprise.api_create_agent` | `autonomous.create_agent` takes precedence |
| GET | `/api/v1/predictions` | `autonomous.get_predictions` <br> `civilization.api_get_predictions` | `autonomous.get_predictions` takes precedence |
| GET | `/api/v1/knowledge` | `autonomous.get_knowledge_graph` <br> `defense.search_articles` | `autonomous.get_knowledge_graph` takes precedence |
| GET | `/api/v1/crisis` | `resilience.api_get_crisis` <br> `command.api_get_crisis` | `resilience.api_get_crisis` takes precedence |

### Impact Analysis
These collisions occur on generic paths due to overlapping domain vocabulary (e.g. both `autonomous` and `enterprise` declaring agents, or `resilience` and `command` declaring crisis). 
- Modern fabrics from Phase 30 onwards use distinct prefixes (e.g. `/api/v1/mission-control/`, `/api/v1/systemic-resilience/`) and are fully isolated.
- The shadowed endpoints are not actively reachable in the default configuration.

---

## Authentication & Authorization Coverage

### 1. JWT Verification (`/api/`)
- All REST endpoints under `/api/v1/` are protected by JWT authentication checks.
- Incoming requests must supply a valid `Authorization: Bearer <token>` header containing `username` and `org_id`.
- Handled at route handler level or through authentication decorators (e.g. `@require_jwt` or equivalent wrapper).

### 2. Admin Authentication (`/admin/`)
- Admin dashboards require active session-based logins.
- Wrapped with the `@require_admin` decorator which verifies the user is authenticated and holds the `admin` role status.

---

## Tenant Isolation Coverage

- The platform enforces tenant boundaries using `OrganizationResolverMiddleware` running on `before_request`.
- Resolves current `organization_id` from the JWT token for API requests or context variables.
- Query filters are automatically scoped to the resolved `organization_id` (via the `TenantMixin` or service-level query filters).
- Handlers validate that target object `organization_id` matches the session/token `organization_id` before allowing updates, deletions, or reads.
