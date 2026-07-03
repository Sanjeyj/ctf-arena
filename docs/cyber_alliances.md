# Cyber Alliances Protocol Guide

## Overview

The Cyber Alliances layer coordinates mutual defense networks, trust indices, and cooperative validations between cyber nations.

---

## Defense Alliances

Each alliance profile is registered using `DefenseAlliance`:

- `alliance_name` — Unique trans-national mutual defense league title.
- `members` — Comma-separated listing of cyber nations.
- `trust_score` — Bilateral trust index calibration rating `[0.0, 1.0]`.
- `status` — `active` | `disbanded` | `suspended`.

---

## Alliance Validation API

Alliances are validated using `AllianceService.validate(alliance_id)`:

```python
# Validate alliance configuration and membership integrity
validation = AllianceService.validate(alliance_id=1)
# Returns: {'valid': True, 'member_count': 3, 'trust_score': 0.75, ...}
```

Validation criteria:
- Alliance status must be set to `active`.
- Membership must contain at least `2` participating cyber nations.
