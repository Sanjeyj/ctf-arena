# Enterprise Cyber Resilience Scorecard

The Resilience Engine computes an aggregate rating representing an organization's capability to withstand, respond to, and recover from cybersecurity threats.

## Model

### ResilienceScore
- Stores calculations and telemetry metric logs.
- Fields:
  - `response_time`: Incident response latency index (0 to 100).
  - `risk`: Risk register mitigation progress index.
  - `controls`: Audit compliance controls passed index.
  - `training`: LMS training completion index.
  - `incidents`: Incident rate safety index.
  - `resilience`: Aggregated Index rating.

## Index Calculation Formula

The final aggregated index is calculated as a weighted sum of the components:

$$\text{Resilience} = 0.2 \times \text{ResponseTime} + 0.3 \times \text{Controls} + 0.2 \times \text{Incidents} + 0.1 \times \text{Training} + 0.2 \times \text{Risk}$$

## REST API Endpoints

- `GET /api/v1/resilience` - Get the latest calculated scorecard.
- `POST /api/v1/resilience/calculate` - Trigger new scorecard recalculation.
