# Plugin Lifecycle & Runtime Environment — CDP v2.0

## 1. Plugin Lifecycle States

Plugins transition through structured lifecycle states managed by the platform runtime:

```
[Discovered] ──> [Loaded] ──> [Validated] ──> [Active] ──> [Suspended / Unloaded]
```

---

## 2. Sandbox Runtime Environment

To prevent plugin failures from affecting core services, plugins execute in an isolated runtime environment:

- **Isolated Process execution**: Plugins run inside isolated worker sub-processes.
- **Resource Constraints**: Limits CPU and memory usage to prevent performance issues.
- **API Access Controls**: Access is restricted to the platform API Gateway.
