# Autonomous SOC Agent Design — CDP v2.0

## 1. SOC Agent Hierarchy

The autonomous SOC divides tasks across specialized agents to process alerts:

```
                  [SOC Orchestrator Agent]
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
[Ingestion Agent]      [Analysis Agent]    [Response Agent]
  (Alerts parser)       (Logs correlation)   (Mitigations)
```

---

## 2. Agent Responsibilities

- **SOC Orchestrator Agent**: Manages active investigations and delegates tasks.
- **Ingestion Agent**: Formats logs and normalizes variables from incoming streams.
- **Analysis Agent**: Correlates alerts and searches logs to locate indicators of compromise.
- **Response Agent**: Selects mitigation plays and queries readiness indicators to verify action safety.
