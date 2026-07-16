# Component Architecture — Cyber Defense Platform v2.0

## 1. Domain-Driven Design (DDD) Components

Inside each microservice container, clean code principles divide components by responsibility.

---

## 2. Core Service Component Layout

```
[HTTP/Event Router] ──> [Application Controller] ──> [Domain Services] ──> [Infrastructure / Repositories]
```

### 2.1 Interface Adapters
- **Controllers & Resolvers**: Receive HTTP/gRPC requests, parse parameters, and dispatch to services.
- **Event Listeners**: Subscribe to Kafka events and map payloads to domain entities.

### 2.2 Core Domain Components
- **Domain Entities**: Encapsulate business logic, validations, and state properties.
- **Policy Evaluators**: Implement specialized domain rules (e.g. Zero-Trust Access, NIST Compliance criteria).
- **Service Domain Aggregates**: Orchestrate interactions across multiple entities within the same database scope.

### 2.3 Infrastructure Adapters
- **Repository Implementations**: Query database tables using abstract data access patterns.
- **AI Integrators**: Connect domain flows to AI prompt chains with built-in output filters.
