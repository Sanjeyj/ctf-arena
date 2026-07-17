# Quality Metrics & Gates
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines the quality metrics and automated check gates for the CTF Arena v1.0.0 codebase.

---

## 1. Quality KPIs

The platform codebase must satisfy the following metrics:

| Metric | Target Value | Verification Tool |
|--------|--------------|-------------------|
| **Code Coverage** | **> 85%** | `pytest-cov` |
| **Linting & Code Style** | Zero errors | `flake8` / `black` |
| **Security Scanning** | Zero High/Critical vulns | `trivy` / `bandit` |
| **Complexity Gate** | Maintainability Index > 75 | `radon` |

---

## 2. Automated Pipeline Gates

To prevent regressions, the CI/CD pipeline enforces three block gates:

### Gate 1: Syntax & Lint check
Runs `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`. Must return exit code 0.

### Gate 2: Code Coverage Gate
Runs `pytest --cov=app --cov-fail-under=85`. Any commit dropping coverage below this line is blocked.

### Gate 3: DOM Certification Check
Runs `python scripts/final_dom_certification.py`. All 236 checks must pass cleanly.
