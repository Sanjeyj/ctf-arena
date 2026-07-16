# Predictive Posture & Risk Forecasting Models — CDP v2.0

## 1. Posture Degradation Model

The predictive engine models how posture scores degrade over time if controls remain unpatched:

```
Post(t) = Post_0 * e^(-alpha * t)
```

- **Post_0**: Initial posture score.
- **alpha**: Degradation factor calculated from active vulnerability findings and threat actor activity indices.

---

## 2. Incident Likelihood Model

Calculates incident likelihood based on asset exposure, active threat campaigns, and control verification history:

- **Parameters**: Combined metrics of internet exposure, unmitigated vulnerabilities, and recent wargame failures.
- **Output**: Forecasts incident probability over a 30-day window.
