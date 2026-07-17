# Release Manifest — v1.0.0
# CTF Arena — EthicBids Technologies™

---

## 1. Release Identity

| Field | Value |
|---|---|
| **Platform** | CTF Arena — Cyber Defense Platform |
| **Maintainer** | EthicBids Technologies™ |
| **Version** | `v1.0.0` |
| **Git Tag** | `v1.0.0` |
| **Release Date** | 2026-07-17 |
| **Release Type** | General Availability (GA) |
| **Release Status** | CERTIFIED — PRODUCTION LIVE |
| **Migration Head** | `8bce79803ffc` |

---

## 2. Certification Summary

| Suite | Count | Result |
|---|---|---|
| **Regression Tests (pytest)** | 1609 | **1609 / 1609 PASS** ✅ |
| **DOM Certification** | 236 | **236 / 236 PASS** ✅ |
| **Production Health Check** | 20 | **20 / 20 PASS** ✅ |

---

## 3. Release Components

| Component | Version | Notes |
|---|---|---|
| Flask Application | v1.0.0 | Release-frozen |
| Gunicorn WSGI Server | 21.2.0 | Production config applied |
| PostgreSQL | 16-alpine | Migrations verified |
| Redis | 7-alpine | Authenticated |
| Nginx | 1.27-alpine | TLS + security headers |
| Prometheus | v2.51.2 | Active scrapes |
| Grafana | 10.4.2 | Dashboards provisioned |

---

## 4. Git Tag Procedure

```bash
# Create signed release tag
git tag -s v1.0.0 -m "Release: CTF Arena v1.0.0 — EthicBids Technologies™
Production Certified: 2026-07-17
Regression: 1609/1609 PASS
DOM Cert: 236/236 PASS
Migration Head: 8bce79803ffc"

# Push tag to remote
git push origin v1.0.0
```

---

## 5. Software Bill of Materials (SBOM)

Full SBOM is available at: `release/SBOM.json`

All runtime dependencies pinned to exact versions in `requirements.txt`. No floating version ranges used in production lock file.

---

## 6. Change Freeze Notice

> [!IMPORTANT]
> The `v1.0.0` branch is **production frozen** from this point forward.
> All new development must be performed in `feature/v2` or `research/` branches.
> Any production patch must follow the `hotfix/v1.0.x-*` workflow defined in `maintenance/security_patch_policy.md`.
