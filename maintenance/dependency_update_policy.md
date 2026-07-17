# Dependency Update Policy
# CTF Arena v1.0.0 — EthicBids Technologies™

This policy dictates how third-party dependencies are tracked, evaluated, and updated for CTF Arena v1.0.0.

---

## 1. Dependency Cadence

Updates are categorized into three tracks:

### A. Emergency Security Updates
* **Trigger**: Critical vulnerability (CVSS >= 9.0) affecting active modules.
* **Timeline**: Action within **24 hours** of discovery.
* **Process**: Direct replacement of the affected library, full regression run, and hotfix deploy.

### B. Minor/Patch Updates
* **Trigger**: Standard bug fixes or performance improvements.
* **Timeline**: Action **Monthly** during the maintenance window.
* **Process**: Updates restricted to patch versions (`x.y.Z`) to avoid breaking API changes.

### C. Major Updates
* **Trigger**: Upgrades to core runtimes (e.g., Python, PostgreSQL).
* **Timeline**: Action **Bi-Annually** or on new release cycle.
* **Process**: Requires architectural RFC approval, staging deployment, and complete regression validation.

---

## 2. Vulnerability Auditing Tools

Platform operators must run these tools weekly:

* **pip-audit**: Scans the python virtual environment for known vulnerabilities.
  ```bash
  pip-audit -r requirements.txt
  ```
* **Safety**: Command-line check against the Safety DB.
  ```bash
  safety check -r requirements.txt
  ```
* **Dependabot**: Automatically configured on the GitHub repository to send alerts and pull requests for outdated packages.
