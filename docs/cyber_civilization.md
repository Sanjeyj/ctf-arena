# Cyber Nation & Civilization Platform Guide

## Overview

The Cyber Civilization Platform represents the maturity modeling of autonomous systems, cyber national demographics, and the overall resilience of the digital ecosystem.

---

## Cyber Nations

Simulated demographics and nation tracking are managed using the `CyberNation` model:
*   `name` — Friendly name of the cyber nation entity.
*   `region` — Deployment region configuration block.
*   `maturity_score` — Float tracking security maturity baseline index.
*   `population` — Simulated demographic participant count.
*   `status` — `active` | `offline` | `quarantine`.

---

## Composite Civilization Metrics

Civilization indexing compiles multiple sectors into a unified rating via `CivilizationMetric`:

| Index Category | Purpose |
|---|---|
| Maturity | Global national maturity averages (target: >=0.65) |
| Resilience | Disaster recovery objectives compliance |
| Intelligence | Share rate of threat intelligence feeds |
| Innovation | Project timelines completion rate |

---

## Service API

```python
# Evaluate baseline indices
metrics = CivilizationService.evaluate(org_id=1)

# Benchmark maturity variance
benchmark = CivilizationService.benchmark(org_id=1)
# Returns: {'variance': +0.12, 'status': 'above_average', ...}

# Compute civilization composite index
composite = CivilizationService.calculate(org_id=1)
```
