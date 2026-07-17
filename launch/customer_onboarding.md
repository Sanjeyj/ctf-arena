# Customer Onboarding Package
# CTF Arena v1.0.0 — EthicBids Technologies™

This document provides the complete onboarding bundle for administrators and participants joining the production CTF Arena platform.

---

## 1. Platform Access Details

| Role | Login URL | Initial Credentials |
|------|-----------|---------------------|
| **Administrator** | `https://arena.ethicbids.app/admin/login` | Configured during seeding — see private credential sheet |
| **Participant** | `https://arena.ethicbids.app/register` | Self-service registration |

---

## 2. Administrator Quick-Start

### First Login Tasks
1. Log in at `/admin/login` using the seeded administrator password.
2. Immediately change the administrator password in the Admin -> Settings panel.
3. Review seeded challenge categories and confirm correct point values.
4. Set event start/end times if applicable.
5. Publish a welcome announcement via Admin -> Announcements.

### Reference Guides
- Full operational guide: `release/OPERATIONS_GUIDE.md`
- Challenge configuration: `release/ADMINISTRATOR_GUIDE.md`
- Incident response: `release/INCIDENT_RESPONSE_GUIDE.md`

---

## 3. Participant Quick-Start

1. Navigate to `https://arena.ethicbids.app/register`.
2. Create a unique username and secure password.
3. Access the **Challenges** panel from the navigation bar.
4. Solve challenges and submit flags in the `flag{...}` format.
5. Track real-time rankings on the **Scoreboard** page.

### Reference Guides
- Participant training: `release/PARTICIPANT_GUIDE.md`
- FAQ: `customer/faq.md`

---

## 4. Demo Challenges (Included at Launch)

The platform ships with a default challenge set across 5 categories:

| Category | Count | Difficulty |
|----------|-------|-----------|
| Web | 3 challenges | Easy — Medium |
| Cryptography | 3 challenges | Easy — Medium |
| Reverse Engineering | 2 challenges | Medium |
| Forensics / Stego | 2 challenges | Easy |
| Pwn | 2 challenges | Hard |

Demo flags use the format `flag{demo_<challenge_slug>}` and can be updated by administrators post-launch.

---

## 5. Support Portal

| Channel | Contact |
|---------|---------|
| **Email Support** | support@ethicbids.app |
| **Documentation Portal** | `https://arena.ethicbids.app/docs` |
| **Emergency Hotline** | +1-800-ETHICBID (Enterprise customers only) |
| **Discord Community** | `https://discord.gg/ethicbids` |
