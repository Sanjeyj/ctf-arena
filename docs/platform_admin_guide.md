# Platform Administration Guide

## 1. System Operations

The platform administration interface provides control over security, wargames, compliance, and user roles.

---

## 2. Managing Challenge Campaigns

### 2.1 Challenge Creation
- Navigate to `/admin/challenges` to register new challenge categories, tags, descriptions, and point values.
- Set verification flags and validation regex parameters.

### 2.2 Re-scoring & Resetting
- Submissions can be recalculated globally if a challenge flag is updated.
- Use the Reset console in the main dashboard to clear participant submission records.

---

## 3. Mission Control & Release Management

- Access `/admin/mission-control` to verify system validation metrics.
- Before deployment, human reviews must approve every active release gate (`ReleaseGateDecision` model) by signing off on target outcomes.
- Track current database migrations and verification states.
