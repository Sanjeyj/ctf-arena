# Security Architecture & Trust Boundaries

Logical segmentation of platform capabilities into security architecture zones.

## Concepts

### ArchitectureZone
Logical segmentation boundary containing assets (e.g. `public`, `edge`, `application`, `data`).

### TrustBoundary
Declared parameters governing communications traversing zone intersections.
- Governed by control requirements definitions list (`control_requirements_json`).

## Validation
Validation checks are evaluated against compliance control checks to determine if boundary conditions are met.

## REST APIs

### POST `/api/v1/exposure-fabric/zones`
Registers a zone.

### POST `/api/v1/exposure-fabric/boundaries`
Registers a boundary.
