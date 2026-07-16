# Cyber Digital Twin Architecture — CDP v2.0

## 1. Digital Twin Domains

The digital twin models corporate IT infrastructure, identities, risks, and security operations to simulate attacks and predict failures:

```
                  [Cyber Digital Twin Core]
                              │
    ┌──────────────┬──────────┴───┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼              ▼
[Infra Twin]   [Identity Twin] [Risk Twin]    [SOC Twin]    [Business Twin]
  (Networks)     (Accounts)   (Quantify)     (Alerts)       (Processes)
```

---

## 2. Twin Categories

- **Infrastructure Twin**: Simulates network Topologies, endpoints, firewalls, and active services.
- **Identity Twin**: Simulates user permissions, group memberships, and role assignments.
- **Risk Twin**: Simulates security posture metrics and vulnerability exposure profiles.
- **SOC Twin**: Simulates alert flows and incident correlation logs.
- **Business Twin**: Models business dependencies, critical services, and downtime impact parameters.
