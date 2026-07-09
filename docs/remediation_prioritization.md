# Remediation Prioritization Workflows

Calculates priority and remediation metrics based on severity weights, asset business impact, and coverage maps.

## Prioritization Formulas

Priority weight score is calculated dynamically during plan registration:

$$Score = ImpactScore \times SeverityWeight$$

Where severity weights are:
- `critical`: 4.0
- `high`: 3.0
- `medium`: 2.0
- `low`: 1.0

## REST APIs

### POST `/api/v1/exposure-fabric/remediation`
Generates a prioritized remediation plan.

### POST `/api/v1/exposure-fabric/remediation/<id>/approve`
Approves a remediation plan.
