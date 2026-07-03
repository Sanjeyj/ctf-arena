# Global Security Intelligence Network Guide

## Overview

The Global Security Intelligence Network (GSIN) provides a federated platform for
worldwide intelligence sharing, cross-organization threat correlation, and collective
cyber defense analytics.

---

## Architecture

```
Global Security Intelligence Network
├── Intelligence Sources       → government, commercial, open-source, private
├── Intelligence Reports       → ingested, normalized, correlated reports
├── Global Threat Feeds        → persistent feed registrations with trust scoring
├── Intelligence Graph         → federated security knowledge graph nodes
└── Federation Layer           → cross-org sharing, subscriptions, synchronization
```

---

## Intelligence Ingestion Pipeline

1. **Ingest** — `IntelligenceService.ingest(data, source_id, org_id)`
   - Accepts raw JSON intelligence payloads
   - Normalizes severity, confidence, and source fields
   - Stores as an `IntelligenceReport` record

2. **Normalize** — `IntelligenceService.normalize(raw)`
   - Maps severity aliases (`info→low`, `warning→medium`, `alert→high`)
   - Clamps confidence to `[0.0, 1.0]`
   - Returns a canonical dict for storage

3. **Correlate** — `IntelligenceService.correlate(report_id)`
   - Finds related reports matching same severity
   - Returns top-10 correlated report dicts

---

## Federation

Cross-organization intelligence sharing is managed by `FederationService`:

| Action | Method | Effect |
|---|---|---|
| Share a report | `share(report_id, target_org_id)` | Creates a federated copy with 5% confidence decay |
| Subscribe to a source | `subscribe(source_org_id, org_id)` | Registers `IntelligenceSource` of type `federated` |
| Synchronize | `synchronize(org_id)` | Pulls report counts from all active subscriptions |

---

## Safety Guardrails

- Simulation-only: no live external intelligence connections
- All reports are tenant-scoped via `organization_id`
- Human approval required before federation sharing
- Full audit trail via `created_at`/`updated_at` timestamps
