# Security Hardening Guidelines — CDP v2.0

## 1. Secure Coding Practices

- **Input Sanitization**: All user inputs are validated against schema constraints before database entry.
- **SQL Injection Prevention**: Use parameterized queries only. Raw SQL strings are blocked by linter rules.
- **CSRF & Security Tokens**: All mutation endpoints require CSRF checks.
- **Zero-Trust Validation**: Verify user scopes and roles for all resource lookups.

---

## 2. Dependency Auditing

- **Vulnerability Checks**: Enforces daily safety audits using `pip-audit` to detect vulnerability alerts.
- **No Outer Connection**: Ensure dependencies remain local and do not initiate external connections.
