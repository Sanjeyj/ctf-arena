# Threat Forecasting Guide

## Overview

The Threat Forecasting Engine uses registered `PredictionModel` instances to generate
probabilistic `ForecastEvent` records that estimate future threat likelihood and impact.

---

## Prediction Models

Each `PredictionModel` tracks:

- `model_name` — Friendly name of the ML model
- `version` — Semantic version (`1.0.0`, `2.1.3`, etc.)
- `accuracy` — Historical test accuracy `[0.0, 1.0]`
- `confidence` — Model's confidence calibration factor

---

## Forecast Events

A `ForecastEvent` is produced by `ForecastService.predict()` and contains:

| Field | Description |
|---|---|
| `prediction` | Plain-language prediction statement |
| `probability` | Estimated likelihood `[0.0, 1.0]` |
| `impact` | Expected impact: `low`, `medium`, `high`, `critical` |
| `confidence` | Model confidence at time of prediction |

---

## Forecast API

```python
# Generate a new forecast
event = ForecastService.predict('ransomware', org_id=1)

# Score a forecast event
score = ForecastService.score(event.id)
# Returns: {'composite_score': 0.785, 'risk_level': 'high', ...}

# Get plain-language explanation
explanation = ForecastService.explain(event.id)
```

---

## Impact Calculation

Impact is derived from the probability value:

| Probability | Impact |
|---|---|
| `< 0.25` | low |
| `0.25 – 0.49` | medium |
| `0.50 – 0.74` | high |
| `>= 0.75` | critical |
