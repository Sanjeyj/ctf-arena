# Ecosystem Trust Federation

This guide describes trust bridging capabilities between organizations.

---

## 1. Trust States
Establishment of link bridges follows three statuses:
- **trusted**: Active bridge, sharing enabled.
- **blocked**: Explicit denial, traffic blacklisted.
- **pending**: Awaiting validation authorization.

---

## 2. Shared Capabilities
Bridges can be authorized to delegate:
- **challenge_sharing**: Enable sharing challenges.
- **scoreboard_sharing**: Compile global team score lists.
- **research_exchange**: Access shared actor intelligence reports.
- **training_exchange**: Direct cross-tenant module access.

---

## 3. Trust API
- **URL:** `/api/v1/federation`
- **Method:** `GET`
- **Response (200 OK):**
  ```json
  {
    "federation_links": [
      {
        "id": 1,
        "source_org_id": 2,
        "target_org_id": 5,
        "relationship": "trusted",
        "capabilities": ["challenge_sharing", "scoreboard_sharing"]
      }
    ],
    "count": 1
  }
  ```
