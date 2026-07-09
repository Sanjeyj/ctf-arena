# Systemic Cyber Risk Architecture

This document describes the systemic cyber risk graph modeling, projection overlay framework, and concentration risk analysis engine introduced in Phase 39.

## Non-Duplication Projection Architecture
Instead of replicating existing database entries (such as `PlatformService`, `ThirdPartyVendor`, or `DefenseAlliance`), Phase 39 introduces an analytical overlay model:
- `SystemicRiskNode`: References an existing platform resource via `reference_type` and `reference_id` within a tenant boundary.
- `SystemicDependency`: Maps directed links between these projected risk nodes.

## Centrality & Concentration Metrics
Systemic risk evaluation is computed purely offline against local data:
* **Degree Centrality**: Calculated as the normalized sum of inbound and outbound edges relative to the active graph size.
* **Concentration Points**: Identifies nodes acting as single points of failure (SPOFs) when their dependency count exceeds a specified threshold, and average substitutability scores are low.
