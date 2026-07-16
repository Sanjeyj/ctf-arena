# Graph Queries & Path traversals — CDP v2.0

## 1. Cypher Query Examples

Sample queries for path traversal and threat hunting:

### 1.1 Find Critical Attack Paths
```cypher
MATCH path = shortestPath((source:Asset {internet_exposed: true})-[*..5]->(target:Asset {criticality: "critical"}))
RETURN path, [n in nodes(path) | n.name] AS names
```

### 1.2 Identify Unprotected Vulnerable Assets
```cypher
MATCH (a:Asset)-[:HAS_VULNERABILITY]->(v:Vulnerability)
WHERE NOT (a)-[:PROTECTED_BY]->(:Control)
RETURN a.name, v.cve_id, a.posture_score
```
