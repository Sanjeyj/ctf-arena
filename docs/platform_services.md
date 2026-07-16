# Platform Core Services Registry

## 1. Domain Service Handlers

Business logic is encapsulated in isolated services under `app/services/`.

---

## 2. Active Services

### 2.1 Assurance & Trust Services
- **`AssuranceService`**: Manages verification metrics and assurance case claims.
- **`DevicePostureService`**: Resolves endpoint posture scores and patch verification status.
- **`ZeroTrustLedgerService`**: Decides access requests and writes results to the transaction log.

### 2.2 Validation Services
- **`ValidationCampaignService`**: Coordinates wargame campaigns and playbook readiness checks.
- **`DefenseEffectivenessService`**: Calculates trend deltas and effectiveness indices.

### 2.3 Operations & Observability Services
- **`PlatformServiceHealthService`**: Calculates golden signals (availability, throughput, latency, saturation).
- **`IncidentCorrelationService`**: Gathers alerts, logs root causes, and manages operational incident queues.
- **`TelemetryIngestionService`**: Tracks active streams and logs telemetry details.
- **`DistributedTracingService`**: Constructs call graph spans and measures database execution latency.

### 2.4 Governance & Risk Services
- **`ThirdPartyVendorService`**: Audits supply-chain compliance and registers third-party suppliers.
- **`RiskQuantificationService`**: Executes Monte Carlo simulation iterations to estimate cyber loss values.
