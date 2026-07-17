# Kubernetes Deployment Architecture
# CTF Arena v1.0.0 — EthicBids Technologies™

This document outlines the Kubernetes (K8s) target architecture for deploying CTF Arena v1.0.0 in clustered environments.

---

## 1. Kubernetes Resource Map

```
                     [ Ingress Controller ]
                               │
                               ▼
                        [ App Service ]
                               │
                               ▼
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
  [ App Pod 1 ]          [ App Pod 2 ]          [ App Pod 3 ]
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
                     [ Postgres Service ]
                               │
                               ▼
                       [ DB StatefulSet ]
```

---

## 2. Pod Specifications

The core Flask web application runs as a stateless Deployment:
- **Replica Count**: 2 minimum, scales dynamically.
- **Resource Limits**:
  - CPU: `1000m` limit, `500m` request.
  - Memory: `1Gi` limit, `512Mi` request.
- **Security Context**:
  - `runAsNonRoot: true`
  - `runAsUser: 1001`
  - `readOnlyRootFilesystem: true`
- **Volumemounts**: Persist `/app/uploads` and `/app/logs` using persistent volume claims (PVCs).
