# Contributing to CTF Arena

Thank you for your interest in improving CTF Arena! Follow these guidelines to ensure clean code integration.

---

## Code Style & Formatting

1. **PEP 8**: Follow standard Python conventions.
2. **Modular Architecture**: Put route handlers in Blueprints, query execution in Repositories, and core validation logic in Services.
3. **Database Writes**: Always call `safe_commit()` (never `db.session.commit()`) to prevent broken session transactions.
4. **Datetime Handling**: Use `utcnow()` from `app.extensions` rather than `datetime.datetime.utcnow()` to prevent deprecation warnings.

---

## Running the Test Suite

Before submitting any code changes, ensure all tests pass:

```bash
# Run pytest
python -m pytest -v
```

---

## Submitting Pull Requests

1. Fork the repository and create a descriptive branch.
2. Verify all 96+ tests pass and write new tests for any added features.
3. Keep pull requests focused on a single issue or optimization.
