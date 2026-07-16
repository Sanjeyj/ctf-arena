# Container Architecture — Cyber Defense Platform v2.0

## 1. Modular Services Context

CDP v2.0 utilizes decoupled, containerized services to ensure domain isolation, performance scaling, and resilience.

```
       [Web UI (Vanilla CSS/JS)]
                   │
                   ▼ (HTTPS / WSS)
         [APIGateway (Kong)]
                   │
    ┌──────────────┼──────────────┬──────────────┐
    ▼              ▼              ▼              ▼
[Auth Service] [Wargame SVC] [Risk Engine] [AI Agent SVC]
    │              │              │              │
    └──────────────┼──────────────┴──────────────┘
                   ▼
           [Event Bus (Kafka)]
                   │
                   ▼
        [Observability & Trace]
```

---

## 2. Core Service Containers

### 2.1 API Gateway & Orchestration
- **API Gateway**: Provides single-entry routing, JWT validation, rate limiting, and SSL termination.
- **Workflow Engine (Temporal)**: Coordinates multi-stage wargames, playbook executions, and recovery scripts.

### 2.2 Domain Microservices
- **Authentication Service**: Manages RBAC, user profiles, and organization contexts.
- **Wargame Simulation Service**: Manages threat actors, topologies, attack paths, and wargame score calculations.
- **Risk & Loss Quantification Engine**: Executes Monte Carlo iterations for loss modeling.
- **AI Agent Service**: Coordinates autonomous SOC Copilots, prompt filtering, and evidence summarizations.

### 2.3 Event Bus & Databases
- **Event Bus (Apache Kafka)**: Delivers messages and telemetry events across domains.
- **Databases**: PostgreSQL handles transactional schemas; Neo4j maintains the Cyber Knowledge Graph; Redis caches session objects.
