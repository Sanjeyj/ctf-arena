# CTF Arena v2 — Admin Guide

This guide covers everything an organizer needs to know to set up, run, and
manage a CTF competition on the platform.

---

## Table of Contents

1. [Accessing the Admin Panel](#accessing-the-admin-panel)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Challenges](#managing-challenges)
4. [Managing Users](#managing-users)
5. [Managing Teams](#managing-teams)
6. [Competition Settings](#competition-settings)
7. [Announcements](#announcements)
8. [Scoreboard Controls](#scoreboard-controls)
9. [Docker / Container Challenges](#docker--container-challenges)
10. [Plugins](#plugins)
11. [Audit Log](#audit-log)
12. [CLI Commands](#cli-commands)

---

## Accessing the Admin Panel

Navigate to `http://<your-host>/admin` and log in with your admin credentials.

| Setting | Default |
|---------|---------|
| Username | `admin` (override via `ADMIN_USER` env var) |
| Password | `ctf_admin_2024` (override via `ADMIN_PASSWORD` env var) |

> ⚠️ Change the default password before running a real competition.

---

## Dashboard Overview

The admin dashboard shows:

- **Live statistics**: total users, teams, challenges, submissions, solves.
- **Score distribution chart** (Chart.js): visualises the spread of participant scores.
- **Recent activity feed**: latest flag submissions and user registrations.
- **Competition state indicator**: shows whether the competition is active, paused, scheduled, or ended.

---

## Managing Challenges

### Creating a Challenge

1. Go to **Admin → Challenges → New Challenge**.
2. Fill in:
   - **Title** — displayed on the challenge card.
   - **Category** — select or create a category.
   - **Difficulty** — Easy / Medium / Hard / Insane.
   - **Initial Points** / **Decay Type** — see scoring section below.
   - **Description** — Markdown-formatted challenge description.
   - **Connection Info** — host/port or URL for network challenges.
   - **Flag(s)** — one or more correct flags; choose case-sensitive or regex match.
   - **Hints** — optional paid hints with point cost.
   - **Files** — upload challenge attachments (max 16 MB per file).
3. Set **Visible** to publish the challenge immediately.

### Scoring Modes

| Decay Type | Behaviour |
|------------|-----------|
| `static` | Fixed points; never changes. |
| `legacy_time` | Points decrease by 1 pt per 10 seconds of elapsed competition time. Minimum 10 pts. |
| `dynamic` | Points decay as more teams solve the challenge (configurable floor and half-life). |

### Editing / Deleting

Use **Admin → Challenges → Edit** or the **Delete** button.
Deleting a challenge also removes all associated submissions, flags, hints, and files.

---

## Managing Users

| Action | Location |
|--------|----------|
| View all users | Admin → Users |
| View user profile | Admin → Users → click username |
| Delete a user | Admin → Users → Delete |
| Reset a user's submissions | Admin → Users → Reset Submissions |

Admins can see each user's score, solve count, last login, and IP address
(if login history is enabled).

---

## Managing Teams

| Action | Location |
|--------|----------|
| View all teams | Admin → Teams |
| Disband a team | Admin → Teams → Delete |
| Move a user between teams | Admin → Users → Edit → assign Team |

---

## Competition Settings

Go to **Admin → Competitions** to configure the current event.

| Field | Description |
|-------|-------------|
| **Name** | Competition display name |
| **Start Time** | When the competition begins (UTC) |
| **End Time** | When the competition ends (UTC) |
| **Registration Open / Close** | Registration window |
| **Is Active** | Master on/off switch |
| **Is Paused** | Suspend scoring without ending the competition |
| **Is Archived** | Mark as historical; read-only scoreboard |
| **Allow Practice** | Let users submit flags outside a live competition |
| **Freeze Time** | Freeze the scoreboard display at this timestamp |

### Competition States

The platform derives the current state automatically from the settings above:

| State | Description |
|-------|-------------|
| `draft` | Competition is created but not active |
| `registration_open` | Before start time, within registration window |
| `scheduled` | Before start time, outside registration window |
| `active` | Within start–end time window |
| `paused` | Manually paused by admin |
| `ended` | Past end time |
| `archived` | Manually archived |
| `practice` | No active competition; practice mode |

---

## Announcements

Announcements are displayed to all users on the challenge dashboard.

1. Go to **Admin → Announcements → New Announcement**.
2. Set **Title** and **Content** (Markdown).
3. Optionally set **Scheduled At** to delay publication.
4. Toggle **Published** to make visible immediately.

---

## Scoreboard Controls

| Action | Location |
|--------|----------|
| View scoreboard | `/scoreboard` (public) |
| Freeze the scoreboard | Admin → Competitions → set Freeze Time |
| Reset ALL scores | Admin → Reset (confirmation required) |

> ⚠️ **Score reset is irreversible.** All submissions, points, and solve records
> are permanently deleted. Use only before a competition begins or in development.

---

## Docker / Container Challenges

For challenges that require a running container:

1. **Register a Docker image**: Admin → Docker → Images → Add Image.
   - Set the image name/tag (e.g., `ctf-arena/web-challenge:latest`).
   - Configure exposed ports.
2. **Create a Deployment Profile**: Defines resource limits and environment variables.
3. **Link to a Challenge**: Edit the challenge and set the Docker image and profile.

Users can then start their own isolated container from the challenge page.
Containers are automatically terminated after a configurable TTL (default 30 min).

### Container Status

| Action | Location |
|--------|----------|
| View all running instances | Admin → Docker → Instances |
| Terminate a container | Admin → Docker → Instances → Stop |
| View container logs | Admin → Docker → Instances → Logs |

---

## Plugins

Custom plugins are placed in the top-level `plugins/` directory.
Each plugin directory must contain an `__init__.py` with a `register(app)` function.

Installed plugins are listed at **Admin → Plugins**.

---

## Audit Log

The audit log at **Admin → Audit** records all security-relevant events.

You can filter by:
- **Username** — see all actions taken by a specific user.
- **Action type** — e.g., `login`, `logout`, `challenge_solve`, `admin_action`.
- **Date range** — narrow down by time window.

Audit entries cannot be deleted through the UI.

---

## CLI Commands

Run these from the project root with the virtual environment activated:

```bash
# Database migrations
flask db upgrade              # Apply pending migrations
flask db downgrade            # Roll back one migration

# Seeding
flask seed-challenges         # Seed sample challenges from JSON
flask seed-users              # Seed test user accounts
flask seed-competition        # Create a default competition

# Maintenance
flask prune-instances         # Terminate expired Docker containers
flask reset-scores            # Delete all submissions (use with care!)
flask export-scores           # Export scores to JSON

# Admin
flask create-admin --username admin --password secret
flask list-users
```

Full CLI reference: `flask --help` / `flask <command> --help`.
