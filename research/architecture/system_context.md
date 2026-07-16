# System Context — Cyber Defense Platform v2.0

## 1. Overview

The Cyber Defense Platform (CDP) v2.0 transitions from a monolithic Flask application to a decoupled, event-driven, domain-driven microservices architecture. It provides continuous security validation, automated governance, systemic resilience modeling, and enterprise security wargaming.

---

## 2. External Entities & User Context

```
                   +──────────────────────────────────+
                   |          SecOps Analysts         |
                   +─────────────────┬────────────────+
                                     │
                                     ▼ (Command Console)
+──────────────────+       +──────────────────+       +──────────────────+
|  Third-Party     |<─────>|  Cyber Defense   |<─────>|  External SIEM/  |
|  Integrations    |       |  Platform (CDP)  |       |  SOC Systems     |
+──────────────────+       +─────────┬────────+       +──────────────────+
                                     │
                                     ▼
                   +──────────────────────────────────+
                   |        Simulated Universe        |
                   |      (Local Egress Bound)        |
                   +──────────────────────────────────+
```

- **SecOps & Administrators**: Query capabilities, review risk quantification metrics, coordinate attack path simulations, and configure validation playbooks.
- **Simulated Universe**: Emulates wargames, network Topologies, endpoints, threat actors, and malware research activities within local, isolated boundaries.
- **Third-Party Integrations**: Interact with detection systems, validation engines, and custom telemetry processors via an API Gateway.
- **Security Boundary**: The platform functions in an offline, simulation-only operational mode, preventing egress access or active infrastructure changes.
