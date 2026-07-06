# Reliability Engineering & Service Health

Continuous tracking of Service Level Indicators (SLIs), Service Level Objectives (SLOs), and dependency health mappings.

## Golden Signals Health Calculation

The Platform Control Plane evaluates composite health scores based on Golden Signals: **Availability**, **Latency**, **Error Rate**, and **Saturation**.

$$Score = (\text{Availability} \times 100) - (\text{Error Rate} \times 50) - (\text{Saturation} \times 30) - \text{Latency Penalty}$$

### Health Classifications
- **90–100**: `healthy`
- **75–89**: `warning`
- **50–74**: `degraded`
- **0–49**: `critical`

## Dependency Health Auditing

The service health checker cascades health evaluations to target dependencies using the `ServiceDependency` graph, warning operators of downstream degradation.

## REST APIs

### GET `/api/v1/operations-fabric/health`
Returns composite platform health statistics.

### GET `/api/v1/operations-fabric/health/<service_id>`
Retrieves history logs and dependency trees for a specific service.
