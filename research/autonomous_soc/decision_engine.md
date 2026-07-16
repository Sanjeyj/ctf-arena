# SOC Decision Engine & Validation — CDP v2.0

## 1. Decision Tree & Confidence Evaluation

The decision engine determines if mitigation actions require human approval based on calculated confidence values:

```
[Agent Action Select] ──> [Confidence Evaluation]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼ (Confidence >= 90%)           ▼ (Confidence < 90%)
          [Auto-Execution]              [Human Approval Queue]
```

---

## 2. Confidence Metrics

- **Evidence Completeness**: Checked against playbooks indicators and metrics.
- **Historic Success Rate**: The success rate of the playbook in previous simulations.
- **Criticality Index**: Actions targeting critical business nodes trigger a default human review path regardless of confidence.
