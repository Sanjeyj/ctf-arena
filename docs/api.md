# CTF Arena v2 — API Reference

> All API routes are prefixed with the Blueprint mount point shown per section.
> Authenticated routes require an active session cookie (`session`).
> Admin-only routes additionally require the session user to have `is_admin=True`.

---

## Table of Contents

- [Authentication (`/auth`)](#authentication-auth)
- [Challenges (`/`)](#challenges)
- [Submissions (`/submissions`)](#submissions)
- [Scoreboard (`/scoreboard`)](#scoreboard)
- [Announcements (`/announcements`)](#announcements)
- [Users (`/users`)](#users)
- [Teams (`/teams`)](#teams)
- [Hints (`/hints`)](#hints)
- [Competitions (`/competitions`)](#competitions)
- [Docker / Instances (`/docker`)](#docker--instances)
- [Admin (`/admin`)](#admin)
- [Analytics (`/analytics`)](#analytics)
- [Audit (`/audit`)](#audit)
- [API (v1) (`/api/v1`)](#api-v1)
- [Health (`/health`)](#health)

---

## Authentication `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/auth/login` | — | Render login page |
| `POST` | `/auth/login` | — | Authenticate user; sets session cookie |
| `GET` | `/auth/register` | — | Render registration page |
| `POST` | `/auth/register` | — | Create new user account |
| `POST` | `/auth/logout` | ✓ | Destroy session |
| `GET` | `/auth/change-password` | ✓ | Render change-password page |
| `POST` | `/auth/change-password` | ✓ | Update password |

**Login request body (`POST /auth/login`)**

```json
{ "username": "alice", "password": "S3cr3t!" }
```

**Registration request body**

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "S3cr3t!"
}
```

**Responses:** HTTP redirects for HTML forms; JSON `{ "success": true }` on AJAX.

---

## Challenges `/`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | ✓ | Dashboard — lists all visible challenges |
| `GET` | `/challenges/<id>` | ✓ | Detail page for one challenge |
| `GET` | `/challenges/<id>/files/<filename>` | ✓ | Download a challenge attachment |

**Query parameters for `GET /`**

| Param | Type | Description |
|-------|------|-------------|
| `category` | string | Filter by category slug |
| `difficulty` | string | Filter by difficulty |
| `q` | string | Full-text search on title/description |

---

## Submissions `/submissions`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/submissions/submit` | ✓ | Submit a flag attempt |
| `GET` | `/submissions/my` | ✓ | View own submission history |

**Flag submission body**

```json
{ "challenge_id": 3, "flag": "FLAG{example}" }
```

**Response**

```json
{
  "correct": true,
  "message": "Correct! 🎉",
  "points": 150
}
```

---

## Scoreboard `/scoreboard`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/scoreboard` | — | Render live scoreboard page |
| `GET` | `/scoreboard/api` | — | JSON snapshot of current scores |
| `GET` | `/scoreboard/api/live` | — | Server-Sent Events stream for real-time updates |

**Scoreboard API response**

```json
{
  "standings": [
    {
      "rank": 1,
      "username": "alice",
      "score": 450,
      "solves": 3,
      "last_solve": "2025-10-01T14:32:00"
    }
  ],
  "freeze_time": null
}
```

---

## Announcements `/announcements`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/announcements` | — | List active, published announcements |
| `GET` | `/announcements/<id>` | — | View single announcement |

---

## Users `/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/users/profile` | ✓ | View own profile |
| `GET` | `/users/<username>` | ✓ | View public profile |
| `POST` | `/users/profile/update` | ✓ | Update display name / bio |

---

## Teams `/teams`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/teams` | ✓ | List teams |
| `GET` | `/teams/<id>` | ✓ | Team detail |
| `POST` | `/teams/create` | ✓ | Create a new team |
| `POST` | `/teams/<id>/join` | ✓ | Join a team |
| `POST` | `/teams/<id>/leave` | ✓ | Leave a team |

---

## Hints `/hints`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/hints/<challenge_id>` | ✓ | List available hints for a challenge |
| `POST` | `/hints/<hint_id>/unlock` | ✓ | Unlock a hint (costs points) |

**Unlock response**

```json
{ "hint": "Try encoding as base64 first." }
```

---

## Competitions `/competitions`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/competitions` | — | List competitions |
| `GET` | `/competitions/active` | — | Get the currently active competition |

---

## Docker / Instances `/docker`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/docker/start` | ✓ | Spawn a challenge container |
| `POST` | `/docker/stop` | ✓ | Terminate the user's container |
| `GET` | `/docker/status` | ✓ | Get container status and connection info |

**Start request body**

```json
{ "challenge_id": 7 }
```

**Status response**

```json
{
  "running": true,
  "host": "challenges.example.com",
  "port": 32768,
  "expires_at": "2025-10-01T15:00:00"
}
```

---

## Admin `/admin`

> **Admin-only** — all routes require an active admin session.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin` | Admin dashboard with platform statistics |
| `GET/POST` | `/admin/challenges` | List / create challenges |
| `GET/POST` | `/admin/challenges/<id>/edit` | Edit a challenge |
| `POST` | `/admin/challenges/<id>/delete` | Delete a challenge |
| `GET/POST` | `/admin/users` | List / manage users |
| `POST` | `/admin/users/<id>/delete` | Delete a user |
| `GET/POST` | `/admin/competitions` | Manage competitions |
| `GET/POST` | `/admin/announcements` | Manage announcements |
| `GET` | `/admin/submissions` | View all submissions |
| `POST` | `/admin/submissions/<id>/delete` | Remove a submission |
| `GET` | `/admin/docker/images` | List Docker images |
| `POST` | `/admin/docker/images` | Add a Docker image |
| `GET/POST` | `/admin/plugins` | Plugin management |
| `GET` | `/admin/audit` | Audit log viewer |
| `POST` | `/admin/reset` | Reset all participant scores (DANGEROUS) |

---

## Analytics `/analytics`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/analytics/summary` | Admin | Platform-wide metrics summary |
| `GET` | `/analytics/challenge/<id>` | Admin | Per-challenge solve rate, attempt timeline |
| `GET` | `/analytics/user/<username>` | Admin | Per-user activity heatmap |

---

## Audit `/audit`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/audit/log` | Admin | Paginated audit log entries |

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default `1`) |
| `per_page` | int | Results per page (default `50`) |
| `user` | string | Filter by username |
| `action` | string | Filter by action type |

---

## API v1 `/api/v1`

The internal JSON API is used by the frontend JS and is rate-limited by the
`RATE_LIMIT_API` setting (default 60 req/min).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/challenges` | ✓ | JSON list of all visible challenges |
| `GET` | `/api/v1/challenges/<id>` | ✓ | Single challenge JSON |
| `POST` | `/api/v1/challenges/<id>/submit` | ✓ | Submit flag (JSON API) |
| `GET` | `/api/v1/scoreboard` | — | Scoreboard JSON |
| `GET` | `/api/v1/users/me` | ✓ | Current user info |
| `GET` | `/api/v1/notifications` | ✓ | Pending notifications for current user |

---

## Health `/health`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | — | Liveness probe (returns 200 OK) |

**Response**

```json
{ "status": "ok", "db": "ok" }
```

Returns `503` if the database is unreachable.

---

## Common Error Codes

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Created |
| `302` | Redirect (HTML form responses) |
| `400` | Bad request / validation failure |
| `401` | Not authenticated |
| `403` | Forbidden (not admin, or CSRF mismatch) |
| `404` | Resource not found |
| `429` | Rate-limited |
| `500` | Internal server error |

---

## Rate Limits

| Endpoint group | Default limit |
|----------------|---------------|
| Login / register | 5 req/min |
| Flag submission | 10 req/min |
| REST API (`/api/v1`) | 60 req/min |
| Global | 100 req/min |

Override any limit via the corresponding environment variable (see [deployment guide](./deployment.md)).
