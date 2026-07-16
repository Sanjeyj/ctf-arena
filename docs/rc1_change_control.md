# Release Candidate Change Control (v1.0.0)

**Date**: 2026-07-08  
**Release Candidate Reference**: `v1.0.0-rc1` (commit `cca83fa`)  
**Proposed Final Release Commit**: `072efa2`

---

## Post-RC Changes List

The following changes were introduced after the `v1.0.0-rc1` tag:

### Change 1 — Phase 34-40 Wiring and Hook Registrations

- **Commit**: `072efa2`
- **Changed Files**:
  - `app/__init__.py` — Registered blueprints and CSRF exemptions for Phase 34–40 fabrics.
  - `app/models/__init__.py` — Registered Phase 34–40 models.
  - `app/services/hook_service.py` — Registered hook definitions for Phase 34–39 hooks.
- **Classification**: **Compatibility / Integration Fix**
- **Reason**: These imports and configurations were untracked in the working tree during the RC tagging process. They represent the completion of platform wiring across all implemented phases.
- **Risk**: ⚪ **Low** — no changes to database tables or operational logic. Simply exposes blueprints and registers them with the Flask container.
- **Tests Executed**: Full 1609 regression suite.
- **Approval Requirement**: Approved by release engineer.

---

### Change 2 — Finding Service Hook Iteration Fix

- **Commit**: `072efa2`
- **Changed Files**:
  - `app/services/finding_service.py` — Fixed the hook response iteration logic.
- **Classification**: **Defect Fix**
- **Reason**: The hook invocation in `FindingService` returns a list of dictionaries rather than a single dictionary. Iterating over the list prevents a `KeyError` or unexpected behavior when multiple hooks are registered.
- **Risk**: ⚪ **Low** — defensive programming improvement.
- **Tests Executed**: `tests/test_exposure_findings.py` (all tests passed).
- **Approval Requirement**: Approved by release engineer.

---

## Schema Changes

- **Schema Changes**: `0`
- No migrations were created or modified during the stabilization phase. The migration head remains exactly `8bce79803ffc`.

---

## Change Risk Summary

- All post-RC changes are classified as low-risk integration alignment and minor bug-fixing. No new features or tables were added. The full 1609-test regression suite passes successfully.

---

### Change 3 — Flask Proxy g Import Fix in Admin Routes

- **Changed Files**:
  - `app/admin/routes.py`
- **Classification**: **Defect Fix**
- **Reason**: Added `g` to Flask imports to fix a `NameError: name 'g' is not defined` when checking `g.current_org` in `admin_cyberrange` route.
- **Risk**: ⚪ **Low** — adds standard Flask import.
- **Tests Executed**: `tests/test_cyberrange.py`, full 1609 regression suite.
- **Approval Requirement**: Approved by release engineer.

---

### Change 4 — Database Instance db Import Fix in Admin Routes

- **Changed Files**:
  - `app/admin/routes.py`
- **Classification**: **Defect Fix**
- **Reason**: Added `db` to `app.extensions` import to fix `NameError: name 'db' is not defined` when calling `db.session.query(Hunt)` in `admin_hunts` route.
- **Risk**: ⚪ **Low** — adds standard SQLAlchemy database container import.
- **Tests Executed**: `tests/test_admin.py`, full 1609 regression suite.
- **Approval Requirement**: Approved by release engineer.

---

### Change 5 — Shared Admin Template Context Variables Injection

- **Changed Files**:
  - `app/context_processors.py`
- **Classification**: **Template Context Fix**
- **Reason**: Sub-templates extending `admin.html` expected context variables `stats` and `leaderboard`. Added a global context injector within `utility_processors` for admin sessions to prevent `UndefinedError` when individual routes omitted them.
- **Risk**: ⚪ **Low** — safe fallback defaults prevent template rendering crashes.
- **Tests Executed**: Full 150-route UI smoke test, full 1609 regression suite.
- **Approval Requirement**: Approved by release engineer.

---

### Change 6 — Layout Block Inheritance Fix in Admin Layout

- **Changed Files**:
  - `templates/admin.html`
- **Classification**: **Template Layout Fix**
- **Reason**: Added `{% block title %}` and `{% block content %}` in the main layout (`admin.html`) to allow sub-pages extending it (e.g. `admin_hunts.html`, `admin_malware.html`, `admin_campaigns.html`) to successfully inject their specific page layouts and title tags. Previously, due to the lack of content blocks in `admin.html`, Flask silently ignored the content overrides and rendered the main admin dashboard for all extending sub-routes.
- **Risk**: ⚪ **Low** — standard template layout inheritance structure.
- **Tests Executed**: Full 150-route UI smoke test, full 1609 regression suite.
- **Approval Requirement**: Approved by release engineer.

---

### Change 7 — Batch A UI Modernization (Dark Futuristic Enterprise Design System)

- **Date**: 2026-07-14
- **Changed Files**:
  - `static/css/ui-modernization.css` (**NEW**) — Central CSS design system: 25+ design tokens, glass surfaces, 12-column Bento grid, components (cards, badges, buttons, forms, tables, charts, progress bars)
  - `static/js/ui-shell.js` (**NEW**) — Admin shell JS: collapsible sidebar, mobile drawer, aria state management, active link detection, localStorage persistence
  - `templates/admin.html` — Full modernization: collapsible sidebar nav (`#admin-sidebar`), top command bar, Bento grid dashboard, JS isolation guard (guards Chart.js + polling so child pages cannot throw null errors), legacy CSS compat variables
  - `templates/login.html` — Dark glassmorphic auth card; all original DOM IDs preserved (`#login-form`, `#login-username`, `#login-password`)
  - `templates/admin_login.html` — Enterprise auth card; all original DOM IDs preserved (`#admin-login-form`, `#admin-username`, `#admin-password`, `#btn-admin-login`)
  - `templates/admin_mission_control.html` — Full Bento grid Mission Control page extending modernized shell
  - `backups/ui-modernization/admin.html.pre-modernization` (**NEW**) — Pre-modernization backup
  - `docs/ui_design_system.md` (**NEW**) — Design system reference documentation
  - `docs/ui_dom_verification_report.md` (**NEW**) — Automated DOM verification report
- **Classification**: **UI Modernization / Frontend Only**
- **Reason**: Implement the approved "Dark Futuristic Enterprise + Restrained Glassmorphism + Responsive Bento Grid" UI design directive across Batch A pages, with zero backend logic changes.
- **Risk Assessment**:
  - ⚪ **No backend risk** — no Python, SQL, or route changes
  - ⚪ **No CSRF risk** — all form tokens preserved verbatim
  - ⚪ **No DOM selector risk** — all test-asserted IDs preserved
  - 🟡 **1 UI regression detected and fixed** — `test_rbac_access_restrictions` expected `b"Admin <span>Portal</span>"` but cursor span was nested inside; fixed by moving cursor span out
- **Post-Fix Test Results**:
  - `pytest tests/test_validation_regressions.py` — **10/10 PASS**
  - `scripts/smoke_test.py` — **ALL PASS**
  - `scripts/admin_smoke_test.py` — **ALL PASS**
  - Automated DOM verification — **25 PASS / 0 FAIL**
  - Full `pytest --tb=short -q` — **1609/1609 PASS**
- **Approval Requirement**: Approved by release engineer.

