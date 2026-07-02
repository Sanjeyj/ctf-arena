# MITRE ATT&CK Mapping Reference

CTF Arena's Cyber Range supports mapping simulated events directly to the MITRE ATT&CK Framework.

---

## Mapped Tactics & Techniques

The catalog contains seeded techniques covering the full attack lifecycle:

| Tactic | Technique ID | Technique Name | Mitigation Recommendation |
|---|---|---|---|
| **Initial Access** | `T1566` | Phishing | Email filtration systems, multi-factor authentication |
| **Execution** | `T1059` | Command and Scripting Interpreter | Restrict script execution policies, log command-line execution |
| **Persistence** | `T1078` | Valid Accounts | Enforce password complexity, implement least privilege |
| **Privilege Escalation** | `T1068` | Exploitation for Privilege Escalation | Regular patch management, minimize running services |
| **Defense Evasion** | `T1070` | Indicator Removal on Host | Forward logs to centralized log server |
| **Credential Access** | `T1110` | Brute Force | Account lockout policies, rate limiting |
| **Discovery** | `T1087` | Account Discovery | Restrict access to account listings |
| **Lateral Movement** | `T1210` | Exploitation of Remote Services | Network segmentation, firewalls between subnets |
| **Collection** | `T1114` | Email Collection | Encrypt mail databases, audit server mailbox access |
| **Exfiltration** | `T1048` | Exfiltration Over Alternative Protocol | Monitor egress network traffic, implement deep packet inspection |
| **Impact** | `T1485` | Data Destruction | Maintain offline read-only backups |

---

## Seeding the Catalog

Seeding is non-destructive and initializes on request:

```python
from app.services.mitre_service import MitreService

# Populates the mitre_techniques table if empty
MitreService.seed_techniques()
```

---

## Mapping Events

To map a raw simulation event to the MITRE catalog:

```python
# Mapped in the service layer after the event is persisted
success = MitreService.map_event_to_mitre(event, 'T1566')
# event.technique -> 'Phishing'
# event.technique_id -> 'T1566'
```

---

## Kill Chain Visualization

The dashboard maps chronological events to tactics using `MitreService.get_kill_chain(simulation_id)`, which outputs:

```json
[
  {
    "event_id": 1,
    "tactic": "initial_access",
    "technique_id": "T1566",
    "technique_name": "Phishing",
    "severity": "low",
    "timestamp": "2026-07-02T...",
    "detected": true
  }
]
```

This output powers the heatmap and detail widgets in the Admin Control Panel.
