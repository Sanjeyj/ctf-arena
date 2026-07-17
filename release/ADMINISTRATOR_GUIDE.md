# Platform Administrator Guide
# CTF Arena v1.0.0 — EthicBids Technologies™

This guide details how to configure and administer the CTF Arena v1.0.0 platform using the Admin Panel dashboard.

---

## 1. Accessing the Admin Panel

The Admin Panel is isolated from the participant dashboard.
- **URL**: `https://your-domain.com/admin/login`
- **Initial Credentials**:
  - Seeded Username: `admin` (or matching `ADMIN_USER` environment variable)
  - Seeded Password: Set during initialization via the `ADMIN_PASSWORD` environment variable.

> [!WARNING]
> Do not use default passwords in production. Change the administrator password immediately after the first login.

---

## 2. Managing Users & Teams

### Active User Ledger
1. Navigate to **Admin Panel** -> **Users**.
2. View, edit, or delete active participant accounts.
3. Roles supported:
   * **Admin**: Full read/write access to settings, logs, and database.
   * **Moderator**: Can manage challenges, submissions, and issue announcements.
   * **Participant**: Standard competition user.

### Audit Submissions
- Navigate to **Submissions** to monitor submissions in real-time.
- Use this view to audit potential brute-forcing, flag sharing, or cheating.

---

## 3. Challenge Configuration

Challenges can be seeded automatically via the CLI or managed in the UI.

### Creating Challenges via Admin UI
1. Navigate to **Challenges** -> **New Challenge**.
2. Fill in parameters:
   - **Name**: Unique challenge identifier.
   - **Category**: (e.g., Crypto, Pwn, Web, Reverse, Stego).
   - **Points**: Initial scoring value.
   - **Description**: Support Markdown notation.
   - **Flag**: The correct solution string (e.g., `flag{example_flag}`).
3. Optional configurations:
   - **Dynamic Scoring**: Decay parameters to automatically reduce point values as more participants solve the challenge.
   - **Hints**: Add hints that participants can unlock (can optionally set a point cost).

---

## 4. Platform Customization & Announcements

### Broadcasting Announcements
1. Navigate to **Announcements** -> **Create Announcement**.
2. Write the message content (supports updates, hint releases, or rules changes).
3. Click **Publish** to broadcast the notification live to all active participant dashboards.

### Scoreboard Management
- The scoreboard calculates rankings dynamically based on correct submissions and timestamp records.
- If a participant is disqualified or banned, delete their account or toggle their status to immediately recalculate the scoreboard.
