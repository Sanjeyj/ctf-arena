# CTF Arena AI Cyber Range SDK

Developer and integration guide for the AI-powered Cyber Range.

---

## Overview

The Cyber Range features:

- **AI Attacker (Red Team)**: Simulates multi-stage attacks based on customizable profiles.
- **AI Defender (Blue Team)**: Simulates event triage, alerting, and recommendations.
- **Incident Response Workflow**: Staged response tracking and metrics.
- **MITRE ATT&CK Mapping**: Links simulation events to tactics and techniques.

---

## Service Layer API

### RedTeamAIService

Simulates a Red Team attack step:

```python
from app.services.red_team_ai_service import RedTeamAIService

# Returns a created AttackEvent
event = RedTeamAIService.simulate_attack_step(
    simulation,
    capability='phishing',  # phishing | web_exploitation | privilege_escalation | lateral_movement | persistence
    mode='easy'            # easy | medium | hard | adaptive
)
```

### BlueTeamAIService

Analyzes a logged AttackEvent:

```python
from app.services.blue_team_ai_service import BlueTeamAIService

# Returns a created DefenseAction if detected; else None
action = BlueTeamAIService.analyze_event(
    event,
    soc_level='l2_soc'  # l1_soc | l2_soc | l3_soc
)
```

### IncidentService

Manages security incident lifecycle:

```python
from app.services.incident_service import IncidentService

# Create incident
incident = IncidentService.create_incident("SQL Injection Alert", "XP Cmdshell triggered", sim.id)

# Progress workflow stage
IncidentService.update_stage(incident, 'containment')  # detection | analysis | containment | eradication | recovery | lessons_learned

# Resolve incident
IncidentService.update_status(incident, 'resolved')  # open | investigating | contained | resolved
```

### TimelineService

Generates a chronological feed of simulation milestones:

```python
from app.services.timeline_service import TimelineService

feed = TimelineService.get_timeline(sim.id)
# Returns list of dicts: [ { 'timestamp': ..., 'type': ..., 'title': ..., 'description': ..., 'severity': ... } ]
```

---

## Hook Lifecycle Integration

Plugins can register hooks to intercept range actions:

| Hook Name | When Fired | kwargs |
|---|---|---|
| `before_attack_simulation` | Before an attack step runs | `simulation`, `capability` |
| `after_attack_event` | After an attack event is logged | `event`, `simulation` |
| `before_defense_action` | Before a SOC defense action runs | `event`, `soc_level` |
| `after_incident_close` | After an incident status is set to resolved | `incident` |

---

## Scoring Logic

Points are dynamically allocated to each team's score:

- **Red Team**: Awarded points on attack step generation (+10/20/30/40 based on mode).
- **Blue Team**: Awarded points on event detection (+15 + reaction speed bonus) and incident containment (+10 containment bonus).
