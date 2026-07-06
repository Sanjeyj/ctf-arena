# Universe Timeline Guide

The **Timeline Service** records chronological events of wargames and simulations.

## Event Schema

Every event records:
- `simulation_id`: Run identifier.
- `event_type`: Actions cataloged.
- `score_delta`: Dynamic readiness change.
- `event_time`: Exact event timestamp.

## Replay & Comparison

Supports deterministic step-by-step playback:
```python
from app.services.universe_timeline_service import UniverseTimelineService
replay_data = UniverseTimelineService.replay(simulation_id, org_id=1)
comparison = UniverseTimelineService.compare_runs(sim_id_1, sim_id_2, org_id=1)
```
