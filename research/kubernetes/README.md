# Kubernetes Cyber Range — Research Initiative
# CTF Arena v2.0 — EthicBids Technologies™
# Research Phase | Not for Production

---

## 1. Vision

The Kubernetes Cyber Range provides isolated, ephemeral challenge environments dynamically provisioned per participant. Each lab is a containerized sandbox that auto-cleans after session expiry, enabling fully hands-on, realistic cyber defense exercises at scale.

---

## 2. Core Design Principles

| Principle | Description |
|---|---|
| **Namespace Isolation** | Each participant receives a dedicated Kubernetes namespace with strict NetworkPolicy rules preventing cross-namespace communication. |
| **Ephemeral Labs** | Challenge pods are spun up on-demand and automatically garbage-collected after 2 hours or session expiry. |
| **Dynamic Provisioning** | Challenges define a `ChallengeSpec` (container image, CPU/memory limits, port mappings). The Range Controller provisions resources at runtime. |
| **Auto Cleanup** | A CronJob sweeps expired namespaces every 15 minutes using label-based TTL selectors. |
| **Reproducibility** | Each challenge environment is hermetically sealed. No shared state between sessions. |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CTF Arena v2.0 Backend                    │
│                  (Range Orchestration API)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Kubernetes API
┌──────────────────────────▼──────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Namespace:     │  │  Namespace:     │                  │
│  │  user-alice-001 │  │  user-bob-002   │  ...             │
│  │                 │  │                 │                  │
│  │  [vuln-web-app] │  │  [crypto-lab]   │                  │
│  │  [db-container] │  │  [solver-shell] │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Range Controller (Operator)             │   │
│  │   - watches ChallengeSession CRDs                   │   │
│  │   - provisions / tears down namespaces              │   │
│  │   - enforces TTL and resource quotas                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. ChallengeSpec CRD (Draft Schema)

```yaml
apiVersion: ctfarena.ethicbids.app/v1
kind: ChallengeSession
metadata:
  name: session-alice-web01
  namespace: ctf-range-system
spec:
  participant: alice
  challenge: web-sqli-basic
  ttlSeconds: 7200
  resources:
    cpu: "500m"
    memory: "512Mi"
  image: ghcr.io/ethicbids/ctf-web-sqli:v1.0
  ports:
    - name: http
      containerPort: 80
```

---

## 5. Implementation Roadmap

| Phase | Duration | Deliverable |
|---|---|---|
| **Alpha** | Q1 2027 | Range Controller CRD + 3 challenge images |
| **Beta** | Q2 2027 | Full namespace isolation + NetworkPolicy enforcement |
| **GA** | Q3 2027 | Multi-cluster support, auto-scaling challenge pools |

---

## 6. Status

**RESEARCH PHASE** — Production v1.0.0 untouched.
