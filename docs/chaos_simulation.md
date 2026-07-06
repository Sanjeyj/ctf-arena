# Simulated Chaos Experiments

Resiliency testing of platform control boundaries under load, latency injections, and dependency breakdowns.

## Safety Boundaries

> [!WARNING]
> All chaos engineering experiments are **strictly simulated** inside the database state.
> No real infrastructure disruption, service restarts, port blocking, packet manipulation, or shell script executions occur.

## Simulation Modules

### Latency Injection
Degrades target health score by simulating latency delays (injects 500ms+ response latency).

### Resource Degradation
Simulates memory/CPU exhaustion by writing high saturation (95%+) and error rates (25%+) into health snapshots.

### Cascading Dependency Failure
Breaks upstream communication by failing downstream dependency availability targets (simulates 80% error rates).

## REST APIs

### GET `/api/v1/operations-fabric/chaos`
Lists scheduled experiments.

### POST `/api/v1/operations-fabric/chaos/<id>/simulate`
Executes a simulated run, evaluating resiliency hypotheses.
