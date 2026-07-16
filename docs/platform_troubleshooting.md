# Platform Troubleshooting Guide

## 1. Common Issues

### 1.1 Application Won't Start
- **Symptom**: `flask run` exits immediately with an error.
- **Cause**: Missing environment variable or misconfigured `config.py`.
- **Resolution**: Verify `.env` / `config.py` settings. Ensure `FLASK_APP=run.py` is set.

### 1.2 Database Migration Errors
- **Symptom**: `alembic.exc.MigrationError` during `flask db upgrade`.
- **Cause**: Migration head mismatch or uncommitted changes in models.
- **Resolution**:
  ```bash
  flask db current   # Check current head
  flask db history   # Review linear chain
  flask db upgrade   # Re-apply pending migrations
  ```

### 1.3 Test Suite Failures
- **Symptom**: `pytest` exits with failures.
- **Resolution**:
  - Check for uncommitted schema changes.
  - Re-run migrations on the test database.
  - Inspect `--tb=long` for traceback details.

### 1.4 Admin Page Returns 500
- **Symptom**: A dashboard template crashes with `UndefinedError`.
- **Cause**: A context variable expected in the template is not passed by the route.
- **Resolution**: Check the blueprint view function to ensure all template variables are populated, even if empty lists (`[]`).

### 1.5 Static Assets Not Loading
- **Symptom**: CSS or JS files return 404.
- **Resolution**: Verify the Flask `static_folder` is correctly configured and that `static/css/ui-modernization.css` and `static/js/ui-shell.js` exist on disk.

### 1.6 Sidebar Not Collapsing
- **Symptom**: Sidebar toggle button doesn't respond.
- **Resolution**: Ensure `static/js/ui-shell.js` is loaded correctly. Check browser console for `script error` or `null element` warnings.

---

## 2. Log Locations

| Log Type | Location |
|---|---|
| Flask application logs | Console stdout / `flask run` terminal |
| Database migration logs | `flask db upgrade` stdout |
| Test execution logs | `pytest` stdout or CI artifacts |
| Smoke test output | `python scripts/smoke_test.py` stdout |
