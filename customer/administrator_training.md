# Platform Administrator Training Manual
# CTF Arena v1.0.0 — EthicBids Technologies™

This manual provides administrators with the procedures required to successfully manage and operate the CTF Arena platform.

---

## 1. Quick Start for Admins

### Core Roles
- **Admins**: Edit settings, manage users, modify database files.
- **Moderators**: Monitor scoreboard, release announcements.

### Key Workflows
1. Log in to the isolated Admin Dashboard at `https://your-domain.com/admin/login`.
2. Seed challenges using the CLI:
   ```bash
   flask seed-challenges
   ```
3. Use the **Users** menu to assign roles or disable accounts.
4. Broadcast news flashes on the **Announcements** page.
5. Audit failed submissions in real-time under the **Submissions** tab.
