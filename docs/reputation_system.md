# Cyber Reputation & Tier System

This guide outlines reputation scores and level calculations within the ecosystem.

---

## 1. Reputation Sources
Cyber standing is calculated from:
- **Bug Bounties**: 50 points per accepted finding.
- **Research Reports**: 30 points per compiled CTI document.
- **SOC Cases**: 20 points per triaged case ticket.
- **LMS Badges**: 15 points per completed certificate course.

---

## 2. Reputation Levels
Standing points map to the following career tiers:
- **Diamond**: 1000+ points.
- **Platinum**: 500 - 999 points.
- **Gold**: 250 - 499 points.
- **Silver**: 100 - 249 points.
- **Bronze**: 0 - 99 points.

---

## 3. Query Standing API
- **URL:** `/api/v1/reputation?user_id=<user_id>`
- **Method:** `GET`
- **Response (200 OK):**
  ```json
  {
    "reputation": {
      "user_id": 5,
      "bounty_points": 100,
      "report_points": 60,
      "soc_points": 40,
      "badge_points": 15,
      "total_points": 215,
      "tier": "Silver"
    }
  }
  ```
