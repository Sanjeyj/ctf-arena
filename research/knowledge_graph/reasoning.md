# Graph Reasoning & Inference Engine — CDP v2.0

## 1. Inference Rules

The reasoning engine infers transitive relationships on the graph:

```
[User] ── (member of) ──> [Group] ── (has role) ──> [Role] === (Inferred) ===> [User] ── (has role) ──> [Role]
```

---

## 2. Threat & Risk Inference

- **Exposure Cascade**: If node A is vulnerable and node B has an open connection to node A, node B is flagged as having elevated exposure.
- **Control Mitigations**: If a control mitigates a vulnerability, any nodes vulnerable to that threat are flagged as mitigated.
