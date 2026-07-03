# Cyber Marketplace Integration Guide

Welcome to the CTF Arena Marketplace developer reference.

---

## 1. Asset Catalog Categories
The marketplace aggregates the following digital resources:
- **courses**: Educational training pathways.
- **labs**: Mapped sandbox target exercises.
- **plugins**: Custom Docker tools and dashboards.
- **templates**: Configuration profiles.
- **reports**: Advanced CTI intelligence bulletins.

---

## 2. Purchase APIs

### List Marketplace Catalog
- **URL:** `/api/v1/marketplace`
- **Method:** `GET`
- **Response (200 OK):**
  ```json
  {
    "marketplace_items": [
      {
        "id": 1,
        "category_id": 2,
        "name": "Advanced Malware Analysis Course",
        "description": "Full walk-through course...",
        "price": 250,
        "asset_type": "courses",
        "asset_url": "https://assets.ctf-arena.net/courses/malware-analysis",
        "is_active": true
      }
    ],
    "count": 1
  }
  ```
