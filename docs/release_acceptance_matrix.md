# Release Acceptance Matrix (v1.0.0)

**Purpose**: Validates representative integration-level workflows across all 20 major platform domains.  
**Scope**: This matrix covers cross-fabric integration paths, not individual unit tests.  
**Date**: 2026-07-08  
**Status**: ✅ All workflows verified (offline simulation mode)

---

## Domain 1 — Authentication & Authorization

| Property | Detail |
|---|---|
| **Entry Point** | `POST /auth/login` |
| **Auth Required** | None (login endpoint) |
| **Tenant Scope** | N/A (login resolves organization) |
| **Service** | User session service |
| **Model** | `User` |
| **Expected Result** | Session cookie set; redirect to dashboard |
| **Audit Record** | Session creation logged |
| **Offline Safety** | ✅ No external auth provider |
| **Human Approval** | Not required |

---

## Domain 2 — Tenant Management

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/organizations/` |
| **Auth Required** | JWT (admin role) |
| **Tenant Scope** | Global admin operation |
| **Service** | `OrgService` |
| **Model** | `Organization` |
| **Expected Result** | Organization record created; `org_id` returned |
| **Audit Record** | Organization creation event |
| **Offline Safety** | ✅ SQLite only |
| **Human Approval** | Not required |

---

## Domain 3 — SOC Operations

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/hunts/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` from JWT |
| **Service** | `SOCHuntService` |
| **Model** | `SOCHunt` |
| **Expected Result** | Hunt record created; status = `active` |
| **Audit Record** | Hunt lifecycle event |
| **Offline Safety** | ✅ Simulation-only |
| **Human Approval** | Not required |

---

## Domain 4 — Cyber Threat Intelligence (CTI)

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/threat-indicators/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` from JWT |
| **Service** | `ThreatIntelService` |
| **Model** | `ThreatIndicator` |
| **Expected Result** | Indicator ingested; enriched; verdict computed |
| **Audit Record** | Indicator enrichment log |
| **Offline Safety** | ✅ No external TI feeds |
| **Human Approval** | Not required |

---

## Domain 5 — Threat Detection & Playbooks

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/detection-validations/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `DetectionValidationService` |
| **Model** | `DetectionValidation` |
| **Expected Result** | Synthetic signal evaluated; coverage ratio computed |
| **Audit Record** | Detection validation record |
| **Offline Safety** | ✅ Synthetic signals only |
| **Human Approval** | Not required |

---

## Domain 6 — Incident Workflows

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/incidents/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `IncidentCorrelationService` |
| **Model** | `OperationalIncident` |
| **Expected Result** | Incident created; correlated metrics/traces linked; timeline event recorded |
| **Audit Record** | `OperationsTimelineEvent` |
| **Offline Safety** | ✅ No live alerting |
| **Human Approval** | Not required |

---

## Domain 7 — Cloud Security Simulation

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/architecture-zones/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `ArchitectureService` |
| **Model** | `ArchitectureZone` |
| **Expected Result** | Zone created; trust boundary linkage computed |
| **Audit Record** | Zone creation event (hook) |
| **Offline Safety** | ✅ No cloud mutations |
| **Human Approval** | Not required |

---

## Domain 8 — Cyber Range / Wargaming

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/universe-simulations/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `ScenarioEngineService` |
| **Model** | `UniverseSimulation` |
| **Expected Result** | Simulation run record created; events logged step-by-step |
| **Audit Record** | `UniverseEvent` per step |
| **Offline Safety** | ✅ Deterministic simulation |
| **Human Approval** | Not required |

---

## Domain 9 — Unified Defense Universe

| Property | Detail |
|---|---|
| **Entry Point** | `GET /api/v1/universe-posture/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `PostureFusionService` |
| **Model** | `UniverseMetric` |
| **Expected Result** | Composite posture score (0–100) with domain breakdowns |
| **Audit Record** | Metric snapshot |
| **Offline Safety** | ✅ SQLite aggregation only |
| **Human Approval** | Not required |

---

## Domain 10 — Control Plane

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/control-policies/evaluate/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `ControlPolicyService` |
| **Model** | `ControlPolicy` |
| **Expected Result** | Policy evaluated; action = `observe`/`warn`/`deny` returned |
| **Audit Record** | Policy evaluation hook log |
| **Offline Safety** | ✅ No live enforcement |
| **Human Approval** | Not required for evaluation; deny override requires human |

---

## Domain 11 — Assurance Fabric

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/assurance-cases/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `AssuranceService` |
| **Model** | `AssuranceCase` |
| **Expected Result** | Case created; confidence score calculated from linked evidence |
| **Audit Record** | Assurance evaluation hook log |
| **Offline Safety** | ✅ No external attestation calls |
| **Human Approval** | Not required |

---

## Domain 12 — Observability Fabric

| Property | Detail |
|---|---|
| **Entry Point** | `GET /api/v1/service-health/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `HealthService` |
| **Model** | `ServiceHealthSnapshot` |
| **Expected Result** | Composite health score (0–100); status category returned |
| **Audit Record** | Health snapshot record |
| **Offline Safety** | ✅ Simulated golden signals |
| **Human Approval** | Not required |

---

## Domain 13 — Exposure Management

| Property | Detail |
|---|---|
| **Entry Point** | `GET /api/v1/attack-paths/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `AttackPathService` |
| **Model** | `AttackPath` |
| **Expected Result** | DFS traversal paths returned; risk scores computed |
| **Audit Record** | `ExposureTimelineEvent` |
| **Offline Safety** | ✅ No live scanning |
| **Human Approval** | Not required |

---

## Domain 14 — Continuous Validation

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/validation-campaigns/` → `POST /api/v1/validation-executions/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `ValidationCampaignService` → `ValidationEngineService` |
| **Model** | `ValidationCampaign` → `ValidationExecution` → `ValidationCheck` |
| **Expected Result** | Campaign activated; scenario executed; checks logged; effectiveness score computed |
| **Audit Record** | Validation execution + check records |
| **Offline Safety** | ✅ Synthetic execution only |
| **Human Approval** | Not required |

---

## Domain 15 — Quantitative Risk

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/risk-simulations/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `RiskSimulationService` |
| **Model** | `RiskSimulationRun` |
| **Expected Result** | Monte Carlo run completed; ALE, percentiles, VaR computed with fixed seed |
| **Audit Record** | Simulation run record |
| **Offline Safety** | ✅ Seeded simulation; no external data |
| **Human Approval** | Not required |

---

## Domain 16 — Resilience Planning

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/stress-tests/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `StressTestingService` |
| **Model** | `StressTestRun` |
| **Expected Result** | Stressed loss computed; resilience degradation delta calculated |
| **Audit Record** | Stress test run record |
| **Offline Safety** | ✅ Deterministic stress model |
| **Human Approval** | Not required |

---

## Domain 17 — Governance Intelligence

| Property | Detail |
|---|---|
| **Entry Point** | `GET /api/v1/governance-scorecards/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `GovernanceScorecardService` |
| **Model** | `GovernanceScorecard` |
| **Expected Result** | Composite weighted scorecard returned; drift detection status included |
| **Audit Record** | Scorecard metric record |
| **Offline Safety** | ✅ SQLite aggregation only |
| **Human Approval** | Not required |

---

## Domain 18 — Systemic Resilience

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/systemic-resilience/contagion-simulations/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `ContagionSimulationService` |
| **Model** | `ContagionSimulationRun` → `ContagionEvent` |
| **Expected Result** | BFS contagion propagation executed; events logged per step; summary computed |
| **Audit Record** | Per-step contagion event records |
| **Offline Safety** | ✅ Seeded simulation; no live network modeling |
| **Human Approval** | Not required |

---

## Domain 19 — Federation & Collective Resilience

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/systemic-resilience/federation-governance/` → `PUT /.../approve/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `FederationGovernanceService` |
| **Model** | `FederationGovernanceRecord` |
| **Expected Result** | Proposal created; FSM transitions: `proposed → reviewing → approved` |
| **Audit Record** | Federation governance record with approval timestamp |
| **Offline Safety** | ✅ No external federation calls |
| **Human Approval** | ✅ **Required** — `approved_by` field mandatory before `approved` state |

---

## Domain 20 — Mission Control

| Property | Detail |
|---|---|
| **Entry Point** | `POST /api/v1/mission-control/release-baselines/` → `PUT /.../approve/` |
| **Auth Required** | JWT Bearer token |
| **Tenant Scope** | `organization_id` scoped |
| **Service** | `ReleaseBaselineService` |
| **Model** | `ReleaseBaseline` → `ReleaseGateDecision` |
| **Expected Result** | Baseline SHA-256 hash computed deterministically; gate checks pass; human approval recorded |
| **Audit Record** | `ReleaseBaseline` + `ReleaseGateDecision` records |
| **Offline Safety** | ✅ Simulation-only |
| **Human Approval** | ✅ **Required** — release baseline approval requires human identity |

---

## Summary

| Domain | Workflows Verified | Human Approval Required |
|---|---|---|
| Authentication & Authorization | 1 | ❌ |
| Tenant Management | 1 | ❌ |
| SOC Operations | 1 | ❌ |
| CTI | 1 | ❌ |
| Threat Detection & Playbooks | 1 | ❌ |
| Incident Workflows | 1 | ❌ |
| Cloud Security Simulation | 1 | ❌ |
| Cyber Range / Wargaming | 1 | ❌ |
| Unified Defense Universe | 1 | ❌ |
| Control Plane | 1 | Partial |
| Assurance Fabric | 1 | ❌ |
| Observability Fabric | 1 | ❌ |
| Exposure Management | 1 | ❌ |
| Continuous Validation | 1 | ❌ |
| Quantitative Risk | 1 | ❌ |
| Resilience Planning | 1 | ❌ |
| Governance Intelligence | 1 | ❌ |
| Systemic Resilience | 1 | ❌ |
| Federation & Collective Resilience | 1 | ✅ |
| Mission Control | 1 | ✅ |
| **TOTAL** | **20** | **2 domains require human approval** |

**All 20 integration workflows verified. Platform is acceptance-ready for v1.0.0.**
