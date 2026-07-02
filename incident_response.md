# Incident Response Playbook

Operational guide for simulated incident response workflows in the Cyber Range.

---

## Workflow Lifecycle Staging

Incidents transition through 6 distinct stages corresponding to the NIST SP 800-61 Incident Handling Guide:

```
Detection ──► Analysis ──► Containment ──► Eradication ──► Recovery ──► Lessons Learned
```

| Stage | Goal | Action in Range |
|---|---|---|
| **Detection** | Alert identified | Auto-triage creates incident status: `open` |
| **Analysis** | Correlate alerts | Set status: `investigating` |
| **Containment** | Limit damage | Isolate host / block IP (+10 Blue Team bonus) |
| **Eradication** | Remove artifacts | Delete persistence payloads |
| **Recovery** | Restore services | Validate system metrics |
| **Lessons Learned** | Review session | Resolved status logged; triggers close hook |

---

## IR Service Operations

```python
from app.services.incident_service import IncidentService

# 1. Escalating an alert to an Incident
incident = IncidentService.create_incident(
    title="Ransomware Escalation",
    description="Encrypted databases identified on staging hosts",
    simulation_id=sim_id
)

# 2. Moving to Analysis
IncidentService.update_stage(incident, 'analysis')

# 3. Containment
# Moves status to 'contained' and awards +10 bonus points
IncidentService.update_stage(incident, 'containment')

# 4. Eradication & Recovery
IncidentService.update_stage(incident, 'recovery')

# 5. Resolution
# Moves status to 'resolved', stage to 'lessons_learned', sets resolved_at, and triggers after_incident_close hook
IncidentService.update_status(incident, 'resolved')
```

---

## Escalation Auto-Triage

When a high-severity alert is detected by the SOC defender, `IncidentService.auto_triage_incident()` can be called to escalate the event into a fully tracked ticket automatically:

```python
# Auto-triaged incident generated directly from a detected attack event
incident = IncidentService.auto_triage_incident(
    simulation_id=sim.id,
    event_details="T1210: Exploitation of Remote Services detected on db-server-prod"
)
```

---

## Incident Queue Dashboard

Admins monitor active tickets at `/admin/cyberrange/incidents`:

- View open, investigating, contained, and resolved tickets
- Links tickets to active simulation details
- Display reported time and triage status
