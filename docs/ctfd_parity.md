# CTFd Feature Parity Audit — CTF Arena v2

This document compares CTF Arena v2 functionality against the industry standard **CTFd** platform.

---

## 1. Feature Comparison Matrix

| Feature | CTFd | CTF Arena v2 | Implementation Notes |
|---------|------|--------------|----------------------|
| **Users / Auth** | Yes | Yes | Bcrypt passwords, registration, session management, secure lockouts. |
| **Team Mode** | Yes | Yes | Create, join, leave teams; scoreboard aggregates points by team. |
| **Dynamic Scoring** | Yes | Yes | Decays points based on solve count or elapsed time. |
| **Admin Panel** | Yes | Yes | Manage challenges, users, submissions, announcements, container status. |
| **Docker Challenges**| Plugin | **Native** | Native container management (spawning, port mapping, expiry, status). |
| **API** | Yes | Yes | Full REST API endpoints returning structured JSON data. |
| **Tokens / Key Auth**| Yes | Yes | Configurable secret key signing session cookies. |
| **Webhooks** | Yes | Yes | Custom triggers on flag solve or user registrations. |
| **Scoreboard Freeze**| Yes | Yes | Restricts public scoreboard updates past a config timestamp. |
| **Announcements** | Yes | Yes | Instant or scheduled markdown broadcasts on dashboard. |
| **Container Limits** | Plugin | **Native** | CPU and memory ceilings customizable per challenge profile. |
| **Metrics / Health** | No | **Yes** | `/health` and Prometheus‑compatible `/metrics` endpoints. |
| **Audit Logs** | No | **Yes** | Log entries for logins, admin actions, and solve attempts. |

---

## 2. Core Feature Parity Highlights

### 2.1 Team Mode
- **CTFd**: Teams are created, and users can invite members via a shared join code.
- **CTF Arena v2**: Standard team registration and member association. Scoreboard standings automatically sum all team member submissions without double-counting challenge solves.

### 2.2 Dynamic Scoring Engine
- **CTFd**: Offers a dynamic scoring plugin calculating decay based on the number of solves:
  $$P = \max\left(P_{\text{min}}, P_{\text{initial}} - \frac{\text{solves} - 1}{\text{decay}} \times (P_{\text{initial}} - P_{\text{min}})\right)$$
- **CTF Arena v2**:
  - Implements the same dynamic scoring logic.
  - Additionally supports a `legacy_time` decay model that reduces points by 1 pt per 10 seconds of elapsed competition time to incentivize fast solving.

### 2.3 Docker Containers / Isolated Sandbox
- **CTFd**: Requires third-party plugins (e.g. CTFd-whale) and complex Docker swarm setups.
- **CTF Arena v2**: Includes native container provisioning via the Docker SDK. Spawns isolated challenge instances per user, maps host ports dynamically, and prunes expired containers automatically via a background worker.

---

## 3. Advantages of CTF Arena v2

1. **Native Docker Support**: No external plugins required to host containerized binary, reverse, or web exploits.
2. **Built-in System Monitoring**: Exposes Prometheus metrics and structured access logs out of the box, whereas CTFd requires custom logging setup.
3. **Resource Efficiency**: Runs as a lightweight single-process Flask application, consuming less CPU and memory than standard CTFd Docker stacks.
