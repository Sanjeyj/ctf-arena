# Exposure Inventory Management

Exposure Inventory projection mappings of original resources (`Asset`, `UniverseNode`, `PlatformService`).

## Data Model

### ExposureAsset
Represents the mapped projections:
- `asset_reference_type`: String (e.g. `'platform_service'`).
- `asset_reference_id`: Integer reference.
- `internet_exposed`: Boolean flag.
- `business_impact_score`: Weight scale (1.0 to 10.0).

### ExposureFinding
Represents vulnerability and security config anomalies detected on assets.
- `source_type`: Must be defined offline (e.g. `simulation`, `control_gap`, `sbom_metadata`, etc.).

## REST APIs

### GET `/api/v1/exposure-fabric/assets`
Lists all exposed asset projection matrices.

### POST `/api/v1/exposure-fabric/assets`
Registers an asset projection.
