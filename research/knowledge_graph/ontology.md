# Cyber Knowledge Graph Ontology — CDP v2.0

## 1. Ontology Model

The knowledge graph models the relationships between IT assets, identities, vulnerabilities, and security controls:

```
[User Identity] ── (owns) ──> [Device Posture] ── (vulnerable) ──> [MITRE Technique]
                                     │
                             (protected by)
                                     │
                                     ▼
                            [Security Control]
```

---

## 2. Entity Classes

- **Asset**: Network nodes, hosts, endpoints, firewalls, and applications.
- **Identity**: Users, roles, API tokens, and access credentials.
- **Control**: Validation checks, authentication policies, and security gates.
- **Threat**: Known threat actors, software tools, and vulnerabilities.
- **Governance**: Security policies, compliance frameworks, and audit logs.
