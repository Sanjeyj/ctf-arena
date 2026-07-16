# AI Agent Memory Design Specification — CDP v2.0

## 1. Multi-Tiered Memory Architecture

To maintain contextual awareness across long wargame scenarios, agents leverage a multi-tiered memory architecture:

```
[Agent Context]
   ├── Short-Term Memory (In-Memory Thread State / Redis)
   └── Long-Term Memory  (Vector Database / PostgreSQL)
```

---

## 2. Memory Tiers

### 2.1 Short-Term Memory
- **Scope**: Active chat session logs and recent alerts.
- **Storage**: Cached in Redis with a 30-minute expiration limit to optimize token context windows.

### 2.2 Long-Term Memory
- **Scope**: Historical attack playbooks, audit logs, and past simulation results.
- **Storage**: Embeddings are stored in pgvector or a local vector database.

---

## 3. Retrieval & Context Management

- **Semantic Search**: Retrieval queries calculate cosine similarity scores to retrieve relevant historical logs.
- **Pruning**: A background worker summarizes old chat logs to optimize context window performance.
