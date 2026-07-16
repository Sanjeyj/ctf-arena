# Platform SDK Overview — CDP v2.0

## 1. Modular SDK Architecture

The SDK allows developers to extend platform capabilities without modifying core systems:

```
[Core Platform Service] <── Event/gRPC ──> [Plugin Sandbox Layer] ──> [Third-Party Plugins]
```

---

## 2. Supported SDK Modules

- **Detection SDK**: Define custom alert parsers and log ingestion formats.
- **Validation SDK**: Implement custom wargame playbooks and scenario parameters.
- **AI SDK**: Define custom prompt templates and domain knowledge sources.
- **Dashboard SDK**: Build custom web UI panels and glass grids.
- **Integration SDK**: Connect telemetry streams to external SIEM/SOC tools.
