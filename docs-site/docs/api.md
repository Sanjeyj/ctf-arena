# REST API Reference

CTF Arena exposes JSON REST endpoints under the `/api/v1` namespace.

---

## 1. Challenge Endpoints

### Get Challenge Listing
- **Path**: `GET /api/v1/challenges`
- **Authentication**: Required
- **Returns**: Array of active challenges.

```json
[
  {
    "id": 1,
    "legacy_id": "ch_caesar",
    "title": "Caesar's Secret",
    "category": "Cryptography",
    "points": 50,
    "difficulty": "Easy"
  }
]
```

### Submit Flag Attempt
- **Path**: `POST /api/v1/challenges/<id>/submit`
- **Authentication**: Required
- **Body**:
  ```json
  { "flag": "FLAG{sample_flag}" }
  ```
- **Returns**: Correct/incorrect status.

---

## 2. Scoreboard Endpoints

### Get Current Standings
- **Path**: `GET /api/v1/scoreboard`
- **Authentication**: Optional
- **Returns**: Leaderboard ranks and solved challenge timestamps.
