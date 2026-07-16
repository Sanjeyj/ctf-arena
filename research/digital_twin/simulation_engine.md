# Twin Simulation Engine — CDP v2.0

## 1. Simulation Loop

The simulation engine models attack propagation across network nodes to estimate lateral movement paths:

```
[Simulation Parameters] ──> [Path Evaluator] ──> [Lateral Movement Simulation] ──> [Risk Score Updates]
```

---

## 2. Path Evaluation

- **Node Vulnerabilities**: Evaluates lateral movement likelihood based on configuration attributes, open ports, and patch levels.
- **Traversal Calculations**: Uses pathfinding algorithms on the network graph to identify lateral movement routes.

---

## 3. Impact Assessment

- **Business Services Mapping**: Evaluates the business impact of simulated node compromise incidents.
- **Risk Score Updates**: Updates posture ratings and risk metrics based on simulation results.
