# Final API Route Inventory (v1.0.0)

**Date**: 2026-07-08  
**Auditor**: Programmatic Flask URL Map Analyzer  
**Status**: ✅ VERIFIED

---

## 1. Routing Summary

The Cyber Defense Platform (CDP) defines a total of **574 routes** registered across **50 blueprints** (including the root application).

| Route Type | Count | Route Prefix | Protection / Authentication |
|---|---|---|---|
| **API Endpoints** | 340 | `/api/v1/` | JWT Bearer Token validation |
| **Admin Endpoints** | 195 | `/admin/` | Session Cookie + Admin Role validation |
| **Static Assets** | 1 | `/static/` | Public Access |
| **Other / Root** | 38 | `/` | Session-based / Public depending on route |
| **TOTAL** | **574** | — | — |

---

## 2. API Blueprint List

The blueprints registered in `app/__init__.py` include:

1. `auth` — Authentication
2. `challenges` — Standard CTFd challenges
3. `scoreboard` — Scoreboards
4. `api` — Base APIs
5. `ai` — Core AI assistants
6. `organization` — Multi-tenant organization boundaries
7. `cyberrange` — Cyber Range challenges
8. `lms` — LMS modules
9. `soc` — Security Operations Center
10. `research` — Research SDK
11. `ecosystem` — Cyber alliances & federation
12. `autonomous` — Autonomous agents
13. `defense` — Knowledge graphs and defenses
14. `secos` — Security economy
15. `cloud` — Cloud architecture simulation
16. `resilience` — Disaster recovery and self-healing
17. `enterprise` — Enterprise decision support
18. `intelligence` — Threat exchange
19. `civilization` — Reputation system
20. `command` — Global command and control
21. `control_plane` — Control policy & model governance
22. `assurance` — Attestation, SBOMs, & trust scoring
23. `operations` — Chaos engineering & incident triage
24. `exposure` — Zone exposure & attack path mapping
25. `validation_fabric` — Sigma/YARA effectiveness validation
26. `risk_quantification` — Monte Carlo loss simulations
27. `strategic_resilience` — Portfolio knapsack optimization
28. `governance_intelligence` — Objectives & scorecard drift tracking
29. `systemic_resilience` — Systemic risk & BFS contagion simulation
30. `mission_control` — Platform convergence, readiness, & ADR gates

---

## 3. Duplicate Route Collisions

Programmatic scan detected exactly **8 method/path overlaps**. Under Flask's routing rules, when multiple blueprints register the same path and HTTP method, the blueprint registered *first* in `register_blueprints()` shadows the others.

| Method | Path | Overlapping Endpoints | Precedence (Active) |
|---|---|---|---|
| **GET** | `/api/v1/hunts` | `soc.list_hunts` <br> `autonomous.list_hunt_sessions` | `soc.list_hunts` |
| **POST** | `/api/v1/hunts` | `soc.create_hunt` <br> `autonomous.create_hunt_session` | `soc.create_hunt` |
| **GET** | `/api/v1/federation` | `ecosystem.list_federations` <br> `intelligence.api_get_federation` | `ecosystem.list_federations` |
| **GET** | `/api/v1/agents` | `autonomous.list_agents` <br> `enterprise.api_get_agents` | `autonomous.list_agents` |
| **POST** | `/api/v1/agents` | `autonomous.create_agent` <br> `enterprise.api_create_agent` | `autonomous.create_agent` |
| **GET** | `/api/v1/predictions` | `autonomous.get_predictions` <br> `civilization.api_get_predictions` | `autonomous.get_predictions` |
| **GET** | `/api/v1/knowledge` | `autonomous.get_knowledge_graph` <br> `defense.search_articles` | `autonomous.get_knowledge_graph` |
| **GET** | `/api/v1/crisis` | `resilience.api_get_crisis` <br> `command.api_get_crisis` | `resilience.api_get_crisis` |

### Mitigation
These overlaps exist within early-phase blueprints that share resource names. The newer blueprints from Phase 30 onwards use distinct prefixing strategies (e.g. `/api/v1/mission-control/`) which guarantees zero collisions. The shadowed endpoints do not cause runtime crashes but are unreachable.

---

## 4. API Drift Analysis

Comparing against the baseline configuration:
- **New Routes**: `0` (None added during stabilization)
- **Deleted Routes**: `0` (None removed during stabilization)
- **Changed Methods**: `0`
- **Changed Authentication Requirements**: `0`

**Result**: 100% route match. No route drift has occurred.
