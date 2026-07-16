# Deployment Architecture — Cyber Defense Platform v2.0

## 1. Kubernetes-Based Deployment Topology

CDP v2.0 is deployed in a secure, isolated local Kubernetes cluster:

```
                  [External Clients]
                          │
                          ▼ (Port 443)
              [Ingress Controller (HAProxy)]
                          │
                   (HTTPS / WSS)
                          │
                          ▼
       [API Gateway Pods (Kong / isolated namespace)]
                          │
    ┌─────────────────────┼─────────────────────┐
    ▼                     ▼                     ▼
[Auth Service Pods] [Wargame Pods] [AI Copilot Pods]
    │                     │                     │
    └─────────────────────┼─────────────────────┘
                          ▼
       [StatefulSets (Postgres, Redis, Kafka)]
```

---

## 2. Infrastructure Hardening Controls

### 2.1 Egress & Networking
- **Zero-Egress Network Policies**: Strict egress filters prevent network traffic from leaving cluster boundaries.
- **Service Mesh (Istio)**: Enforces Mutual TLS (mTLS) for all internal container communications, preventing unauthorized traffic.

### 2.2 Scaling & High-Availability
- **Horizontal Pod Autoscaling**: Application pods scale dynamically based on CPU/memory usage profiles.
- **Node Affinity**: Stateful components (Kafka, PostgreSQL) are scheduled on dedicated storage nodes, while stateless microservices run on high-compute nodes.
