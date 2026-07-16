# Platform Database Models & Schema Reference

## 1. Overview

The database schema contains 248 tables representing 238 SQLAlchemy classes. Key domains are detailed below.

---

## 2. Core Schema Domains

### 2.1 Participant & Administration Core
- **`User`**: Account identity containing username, email, password hash, role classification, and organization scope.
- **`Team`**: Group of participants solving challenges together.
- **`Challenge`**: Individual wargame task with categories, flag definitions, and points values.
- **`Submission`**: Score record tracking solved challenges.

### 2.2 Assurance & Posture Domain
- **`AssuranceCase`**: Represents validation claims, owner information, and confidence metrics.
- **`ControlValidation`**: Checks control references against actual outcomes, reporting effectiveness scores.
- **`DevicePosture`**: Endpoint patch metadata, OS family, encryption states, and security posture values.
- **`ZeroTrustDecision`**: Ledger tracking resource requests, evaluation metrics, and authorization decisions.

### 2.3 Validation & Threat Intelligence Domain
- **`ValidationCampaign`**: Groups validation campaigns with execution parameters and status logs.
- **`PlaybookReadiness`**: Details playbook coverage statistics and evidence scores.
- **`DefenseEffectiveness`**: Logs metrics, previous scores, and trend directions.

### 2.4 Incident Response & Telemetry Domain
- **`OperationalIncident`**: Lists active system errors, severity levels, and root cause correlations.
- **`TelemetrySource`**: Registers ingestion intervals and ingestion health scores.
- **`TelemetryMetric`**: Logs metric names, types, values, and timestamps.
- **`Span` / `Trace`**: Distributed tracing telemetry detailing service call paths and execution times.
