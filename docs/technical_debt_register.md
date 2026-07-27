# Technical Debt Register
**Release Version:** 1.0.0

The following register lists the dead styling elements, legacy shims, and de-duplicated documentation files to clean up in the Cyber Defense Platform.

---

## 1. Debt Registry Ledger

| ID | Description | Severity | Legacy File | Target Action | Status |
|---|---|---|---|---|---|
| `TD-001` | Dead styling blocks and class declarations | Low | `static/css/ui-modernization.css` | Keep as compatibility shim | Monitored |
| `TD-002` | Obsolete JS listeners and click event handlers | Low | `static/js/ui-shell.js` | Keep as compatibility shim | Monitored |
| `TD-003` | Duplicate documentation sections (grc, resilience) | Medium | `docs/grc.md` | Merge and redirect to Design Bible | Resolved |
| `TD-004` | Legacy `ui-` class references in templates | High | Template files (33 files) | Refactored using migration script | Resolved |

---

## 2. Refactoring Controls
- No backend code changes.
- Fallback CSS shims kept in place to avoid breaking regression healthcheck scripts (which check `ui-modernization.css` and `ui-shell.js`).
