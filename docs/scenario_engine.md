# Scenario Engine Guide

The **Cross-Domain Scenario Engine** allows simulating safe cyber incidents (e.g. ransomware infection, cloud node disruption) to measure baseline resilience and readiness without triggering actual infrastructure changes.

## Safety Constraints

- **No Live Mutation:** Never executes shell commands, code payloads, or live provider modifications.
- **State Updates:** Scenarios write to DB history and adjust metrics only.
- **Deterministic Outcomes:** Returns structured evaluation logs.

## Impact Scoring & Recommendations

Scenarios estimate potential risk drops and suggest mitigation strategies:
```python
from app.services.scenario_engine_service import ScenarioEngineService
impact = ScenarioEngineService.calculate_impact(scenario_id, org_id=1)
controls = ScenarioEngineService.recommend_controls(scenario_id, org_id=1)
```
