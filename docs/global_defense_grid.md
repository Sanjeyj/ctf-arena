# Global Autonomous Defense Grid Guide

## Overview

The Global Autonomous Defense Grid tracks coverage, system health indicators, and active readiness indicators of autonomous protective node arrays.

---

## Defense Grid Clusters

Each defense cluster is tracked using `DefenseGrid`:

- `name` — Friendly name of the defense grid cluster zone.
- `coverage` — Protective area coverage metric `[0.0, 1.0]`.
- `health` — Cluster performance health indicator `[0.0, 1.0]`.
- `readiness` — Realtime grid defensive readiness score `[0.0, 1.0]`.

---

## Grid Health & Synchronization

Defense grids are synchronized trans-nationally via `AllianceService`:

```python
# Sync and calculate grid readiness percentages
sync_info = AllianceService.synchronize(org_id=1)
# Returns: {'synchronized_percentage': 92.5, 'status': 'operational', ...}
```

### Alerts

- Critical threshold alert triggered if health drops below `0.5`.
- Degraded warning alert triggered if health drops below `0.8`.
