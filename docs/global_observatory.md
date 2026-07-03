# Global Cyber Observatory Guide

## Overview

The Global Cyber Observatory is a distributed monitoring system tracking health and
security posture across five observatories worldwide: Threat, Intelligence, Compliance,
Resilience, and Enterprise.

---

## Observatory Types

| Type | Purpose |
|---|---|
| Threat | Active threat feed monitoring and IOC velocity |
| Intelligence | Intelligence report ingestion rate and quality |
| Compliance | Framework compliance score aggregation |
| Resilience | Business continuity and DR health indicators |
| Enterprise | Autonomous agent and workflow performance |

---

## Node Health Model

Each `ObservatoryNode` tracks:

- `region` — Geographic deployment (`us-east`, `eu-west`, `asia-south`, `private-cloud`)
- `node_type` — Observatory classification (see table above)
- `status` — `online` | `degraded` | `offline`
- `health` — Float `0.0` to `1.0` representing combined node health

### Health Thresholds

| Health Range | Status |
|---|---|
| `>= 0.7` | Healthy / Online |
| `0.5 – 0.69` | Degraded (auto-set by alert) |
| `< 0.5` | Critical / Offline |

---

## Observatory API

```python
# Monitor all nodes for an org
ObservatoryService.monitor(org_id=1)

# Aggregate health for a region
ObservatoryService.aggregate('us-east')

# Trigger alert if health drops below threshold
ObservatoryService.alert(node_id=1, threshold=0.5)
```
