# Retrieval-Augmented Generation (RAG) Architecture — CDP v2.0

## 1. Context Injection Pipeline

The platform uses a local RAG pipeline to enrich AI agent prompts with verified security metadata:

```
[User Question] ──> [Query Embeddings] ──> [Vector DB Search] ──> [Context Synthesis] ──> [Hardened LLM]
```

---

## 2. Ingestion & Pre-processing

- **Data Sources**: Documents include compliance frameworks, MITRE ATT&CK maps, and platform manuals.
- **Chunking Strategy**: Markdown files are parsed into 500-token chunks with 50-token overlaps to preserve structural headings.
- **Embedding Generation**: Local models convert chunks into vector vectors.

---

## 3. Query Execution & Synthesis

- **Hybrid Retrieval**: Combines BM25 keyword matching with semantic vector search for accurate results.
- **Context Synthesis**: Context blocks are formatted with markdown quotes and appended to the agent's prompt template.
