# High Availability & Fault Tolerance Design
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines the high availability (HA) configuration guidelines and fault tolerance designs for hosting the CTF Arena platform.

---

## 1. High Availability Architecture

```
                  [ External Load Balancer ]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [ App Node A (West) ]             [ App Node B (East) ]
            │                                 │
            └────────────────┬────────────────┘
                             ▼
                [ Active-Standby DB Cluster ]
                             │
                             ▼
                [ Replicated Redis Cluster ]
```

### A. Load Balancing layer
An external application load balancer (e.g. AWS ALB, Cloudflare, or HAProxy) routes traffic to at least two web application nodes across different availability zones.
- Session persistence: Sticky sessions are not required if Redis session storage is enabled.

### B. Database High Availability
PostgreSQL must run in primary-standby mode:
- Primary DB handles all write transactions.
- Standby replica continuously pulls WAL (Write-Ahead Logging) data for synchronous replication.
- Set up auto-failover tooling (e.g. Patroni or pg_auto_failover) to switch traffic to the standby node on primary failure.

---

## 2. Fault Isolation & Redundancy

To insulate the platform from individual container crashes:
- **Liveness Probes**: Automatically restarts containers when the `/health` endpoint stops responding or returns non-200.
- **Readiness Probes**: Prevents traffic routing to new containers until they complete startup/seeding hooks.
- **Cache Persistence**: Redis configured with Append-Only File (AOF) persistence so that rate limits and active session keys survive container reboot.
