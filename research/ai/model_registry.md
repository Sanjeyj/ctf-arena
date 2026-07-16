# Local Model Registry & Policy Governance — CDP v2.0

## 1. Local Registry Overview

The model registry catalogs and version-controls offline LLM models to ensure consistent performance:

```
[Registry Catalog]
   ├── Llama-3-8B-Instruct (Primary Analysis model)
   └── Phi-3-Mini          (Triage & classification model)
```

---

## 2. Policy Governance

- **Parameter Tuning**: Restricts model temperature to `0.0` for analysis tasks to ensure deterministic responses.
- **Evaluation Tracking**: Evaluates models on local datasets to benchmark speed and accuracy.
- **Offline Assurance**: The platform operates in a zero-network configuration, ensuring all models execute on local hardware.
