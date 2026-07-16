# CHANGELOG — Cyber Defense Platform

All notable changes are documented here in reverse chronological order.

---

## [1.0.0] — 2026-07-16

### Added
- 40 backend development phases producing 238 SQLAlchemy models across 248 database tables.
- 574 registered routes: 195 admin routes and 340 API endpoints.
- Unified Dark Futuristic Enterprise UI design system (glassmorphism, responsive Bento grids, WCAG accessibility).
- UI Modernization Batches A, B, C, and D — modernizing all core admin dashboards and operational fabrics.
- Final Release Engineering: Project Health Audit, Frontend, Backend, Security, and Performance Certification documents.
- Complete release package: manifest, SBOM, deployment guide, backup guide, operator checklist.
- Final Platform Certificate.

### Changed
- All admin templates upgraded to use `{% extends "admin.html" %}` shell inheritance.
- Static asset pipeline unified to `static/css/ui-modernization.css` and `static/js/ui-shell.js`.

### Fixed
- Resolved `NameError: name 'g' is not defined` in `admin_cyberrange` route.
- Resolved `NameError: name 'db' is not defined` in `admin_hunts` route.
- Fixed template context variable injection gaps for sub-routes in context processors.
- Fixed `{% block content %}` inheritance allowing 64 sub-templates to override dashboard panels.
- Fixed admin login test assertion for `admin_login.html` cursor span positioning.
