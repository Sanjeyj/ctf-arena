# Security Patch Policy
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines the protocols for identifying, authoring, verifying, and deploying security hotfixes for CTF Arena v1.0.0.

---

## 1. Hotfix Classification

| Class | Severity | SLA for Fix |
|-------|----------|-------------|
| **Critical** | CVSS 9.0 – 10.0 (e.g. Remote Code Execution) | 24 Hours |
| **High** | CVSS 7.0 – 8.9 (e.g. Privilege Escalation) | 72 Hours |
| **Medium** | CVSS 4.0 – 6.9 (e.g. Rate Limit Bypass) | 14 Days |
| **Low** | CVSS 0.1 – 3.9 (e.g. Server Signature Leak) | Next Minor Release |

---

## 2. Hotfix Workflow

To preserve the certified release, all security patches must follow this flow:

```
[Main (v1.0.0)] ──► Branch: hotfix/v1.0.x-descr ──► Write Patch 
                                                            │
[Staging Deploy] ◄── [Regression Gate (1609 tests)] ◄───────┘
       │
[Production Deploy (v1.0.x)]
```

1. **Isolation**: Spin up a dedicated hotfix branch matching the patch version: `hotfix/v1.0.x-<vulnerability>`.
2. **Implementation**: Modify only the code necessary to address the vulnerability. Do not include any unrelated changes.
3. **Verification Gate**:
   - Run the regression test suite: `python -m pytest` (**1609/1609 PASS** required).
   - Run the DOM certification suite: `python scripts/final_dom_certification.py` (**236/236 PASS** required).
4. **Code Review**: Requires approval from at least one Security Lead and one System Architect.
5. **Deployment**: Deploy via GitHub Actions tag validation to the target environment.
