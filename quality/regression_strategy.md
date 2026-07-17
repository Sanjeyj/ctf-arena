# Regression Testing Strategy
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines the testing strategy to prevent feature regressions during updates or patch cycles.

---

## 1. Test Levels & Mapping

The regression pipeline spans three levels of verification:

```
[ Unit Tests ] ────► [ Integration Tests ] ────► [ DOM Cert (E2E) ]
 1400+ asserts         200+ db validations        35 routes / 236 checks
```

### A. Unit Tests (Pytest)
Validate services, models, and utility functions in isolation. Mocking is utilized for external services (like the Docker wargame daemon).

### B. Integration Tests
Exercise database commits, blueprint routings, and transaction rollbacks. Uses a live SQLite/PostgreSQL test client.

### C. End-to-End DOM Certification
Runs the Flask test client and validates that CSS containers, glass cards, sidebar navigation links, and headings render correctly without template errors.

---

## 2. Test Execution Commands

Run before any release tag:
```bash
# Run unit and integration tests
python -m pytest --tb=short -q

# Run E2E DOM certification
python scripts/final_dom_certification.py
```
**Acceptance Criteria**: **100% test pass rate** (1609/1609 pytest, 236/236 DOM checks).
