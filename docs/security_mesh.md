# Security Mesh & Route Latency Weight Mapping

The Security Mesh coordinates trust federation connections and traffic routing weights between multi-region nodes.

## Models

### SecurityMesh
- Tracks federation trust tunnels.
- Fields: `source_region`, `destination_region`, `trust_level`, `status` (active, degraded, offline).

### MeshRoute
- Tracks path latency routing weights.
- Fields: `source_node`, `destination_node`, `weight`, `latency` (in ms), `status`.

## Routing Weight Logic

Tunnels default to `trusted` and `active`. When routes between nodes degrade, latency indices are recalculated, and traffic routing weights are updated dynamically:

$$\text{Optimal Path} = \min \sum (\text{weight} \times \text{latency})$$

## REST API Endpoints

- `GET /api/v1/mesh` - List meshes and routes.
- `POST /api/v1/mesh/establish` - Establish trust federation connection link.
- `POST /api/v1/mesh/route` - Register path routing details.
- `POST /api/v1/mesh/optimize` - Query Dijkstra latency optimized routing paths.
