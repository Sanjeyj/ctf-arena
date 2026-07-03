# Security Knowledge Graph API Reference

This reference guide covers the Security Knowledge Graph.

---

## 1. Graph Node types
The graph compiles nodes matching:
- **actor**: Threat actor profile (origin, motivations).
- **campaign**: Mapped active operations campaigns.
- **malware**: signatures and malware family types.
- **ioc**: indicators (IPs, hashes).
- **detection**: events matching Sigma or YARA signatures.
- **incident**: cases opened.

---

## 2. Relationships (Edges)
Connecting links are catalogued under:
- `Actor → Campaign`
- `Campaign → Malware`
- `Malware → IOC`
- `IOC → Detection`
- `Detection → Incident`

---

## 3. Query Graph API
- **URL:** `/api/v1/knowledge`
- **Method:** `GET`
- **Response (200 OK):**
  ```json
  {
    "graph": {
      "nodes": [
        {"id": 1, "node_type": "actor", "name": "APT28"},
        {"id": 2, "node_type": "campaign", "name": "Operation Windigo"}
      ],
      "links": [
        {"id": 1, "source_node_id": 1, "target_node_id": 2, "relationship": "attributes_to"}
      ]
    }
  }
  ```
