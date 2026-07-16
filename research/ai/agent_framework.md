# AI Agent Orchestration Framework — CDP v2.0

## 1. Multi-Agent Orchestration Flow

CDP v2.0 introduces a collaborative multi-agent architecture for automated security analysis:

```
                  [Coordinator Agent]
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
[Triage Agent]      [Analysis Agent]    [Playbook Agent]
 (Alert Parsing)     (Logs & Traces)     (Remediation)
```

---

## 2. Specialized Security Agents

- **Coordinator Agent**: Receives raw requests, parses intent, assigns sub-tasks to specialized agents, and aggregates results.
- **Triage Agent**: Automatically parses incoming alerts, extracts IP addresses and domain flags, and assigns initial risk weights.
- **Analysis Agent**: Gathers tracing graphs, queries database logs, and detects anomalous activity indicators.
- **Playbook Recommendation Agent**: Reviews readiness indices, references MITRE mappings, and recommends remediation tasks.

---

## 3. Communication Protocol

- **Structured Messaging**: Agents communicate using JSON schemas over Kafka event streams.
- **Human Approval Loop**: Actions that alter platform state (e.g. starting a wargame) require explicit human sign-off before execution.
