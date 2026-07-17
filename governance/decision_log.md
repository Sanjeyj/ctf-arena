# Decision Log — Cyber Defense Platform
# EthicBids Technologies™ | Business Governance

---

## Purpose
This log records all significant product, architecture, commercial, and operational decisions made by EthicBids leadership for audit, accountability, and institutional knowledge preservation.

---

## Decision Record Format

Each entry follows the **ADR (Architecture Decision Record)** pattern:
- **ID**: Sequential identifier
- **Date**: Decision date
- **Status**: Proposed / Accepted / Superseded / Deprecated
- **Context**: Why the decision was needed
- **Decision**: What was decided
- **Consequences**: Impact of the decision

---

## Decision Log

### DEC-001 — Production Code Freeze at v1.0.0
- **Date**: 2026-07-17
- **Status**: Accepted
- **Context**: v1.0.0 achieved 1609/1609 regression pass and 236/236 DOM certification. Risk of regression from further changes outweighs any incremental feature benefit.
- **Decision**: Freeze all production code at v1.0.0. All new features go to `feature/v2/` or `research/` branches.
- **Consequences**: Platform stability guaranteed. Feature velocity shifts to v2.0 branch.

### DEC-002 — Long-Term Support for v1.0.0 (36 months)
- **Date**: 2026-07-17
- **Status**: Accepted
- **Decision**: v1.0.0 receives security patches and dependency updates only for 36 months (until 2029-07-17).
- **Consequences**: Enterprise customers can plan deployments with confidence.

### DEC-003 — Vercel as Primary Serverless Deployment Target
- **Date**: 2026-07-17
- **Status**: Accepted
- **Decision**: Vercel is the recommended serverless deployment platform. Docker stack maintained for self-hosted enterprise.
- **Consequences**: `vercel.json` and `api/index.py` maintained as first-class deployment artifacts.

### DEC-004 — v2.0 Multi-Tenant SaaS Architecture
- **Date**: 2026-07-17
- **Status**: Proposed
- **Decision**: v2.0 will use row-level PostgreSQL tenant isolation. Schema-per-tenant for Enterprise tier.
- **Consequences**: Requires new Alembic migration branch. No impact on v1.0.0.

### DEC-005 — Open Core Licensing Model
- **Date**: 2026-07-17
- **Status**: Proposed
- **Decision**: Community edition released as open-core (MIT). Enterprise features (SSO, white-label, AI Copilot) remain proprietary.
- **Consequences**: Community adoption drives pipeline. Enterprise upsell on advanced features.
