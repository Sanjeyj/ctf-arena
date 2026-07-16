# Graph Schema Specification — CDP v2.0

## 1. Graph Node Property Schema

The graph database schema defines required properties and validation constraints for nodes and edges:

```
[Device Node Properties]
   ├── id: String (Primary Key)
   ├── name: String
   ├── ip_address: String
   └── posture_score: Float
```

---

## 2. Graph Constraints

- **Edge Constraints**: Mapped relationships (e.g. `MEMBER_OF`, `ACCESSES`, `EXPLOITS`) require timestamp properties.
- **Node Constraints**: Node lookups require primary keys to be unique.
