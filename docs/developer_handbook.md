# Cyber Defense Platform Developer Handbook
**Release Version:** 1.0.0
**Design Framework:** AXIOM Core v1.0

This guide outlines directory structures, contribution rules, coding conventions, and local environment setups.

---

## 1. Directory Structure Map

```
ctf-arena/
  ├── app/                  <-- Frozen Backend (Flask Services, Repositories, Models)
  ├── static/
  │     ├── css/
  │     │     ├── axiom.css <-- Master import stylesheet (Tokens, reset, typography)
  │     │     └── ui-modernization.css <-- Fallback CSS shim (regression healthcheck)
  │     └── js/
  │           ├── axiom-shell.js <-- Modular JS Loader (Palette, Rail, Navigation)
  │           └── ui-shell.js    <-- Fallback JS shim (regression healthcheck)
  ├── templates/            <-- HTML Templates (all migrated to AXIOM ax- classes)
  ├── docs/                 <-- Documentation Suite
  └── tests/                <-- Python Test Suite (1609 unit tests)
```

---

## 2. Development Setup

### 2.1 Virtual Environment bootstrap
Build the project virtual environment and resolve dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2 Running Local Verification
Always execute quality verification checks before commits:
```bash
venv\Scripts\python.exe -m pytest
venv\Scripts\python.exe scripts/final_dom_certification.py
```
Both checks must pass cleanly.
