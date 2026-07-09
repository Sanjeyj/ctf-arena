# Logical Attack Path Modeling

Models hypothetical path trajectories traversing the logical topology of security architecture zones.

## Graph Modeling

Vertices represent `ExposureAsset` projections. Edges are inferred from:
1. `ServiceDependency` platform services links.
2. `UniverseLink` node networks.
3. Zone communication boundaries.

## Pathfinding Algorithms

Depth-First Search (DFS) is used to find paths between any two exposed assets:
- Max depth limit prevents performance bottlenecks.
- Visited sets ensure cycle protection.

## REST APIs

### POST `/api/v1/exposure-fabric/paths/critical`
Finds the critical (highest risk score) route between source and target assets.
