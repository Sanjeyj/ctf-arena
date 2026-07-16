# Database & Schema Migration Strategy — CDP v2.0

## 1. Migration Strategy

The migration from the monolithic v1.0 SQLite schema to the decoupled v2.0 PostgreSQL and Neo4j architectures follows a multi-stage approach:

```
[V1.0 SQLite] ──> [Schema Transformer] ──> [Postgres (Relational) & Neo4j (Graph)]
```

---

## 2. Data Transformations

- **Identity Mapping**: User and organization records are exported to the PostgreSQL Auth schema.
- **Topology Mappings**: Network, device posture, and incident logs are converted into nodes and relationships for Neo4j.
- **Verification Gates**: Checksum checks ensure data integrity before database decommissioning.
