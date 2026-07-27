# AXIOM Platform Map & Information Architecture
**Release Version:** 1.0.0

This document structures the complete page, route, and layout architecture of the Cyber Defense Platform.

---

## 1. Primary Navigation Tree

```
[Command Rail - 56px] ──> [Context Panel - 220px] ──> [Workspace]
  ├── Competition
  │     ├── Dashboard (/admin)
  │     ├── Challenges (/admin/challenges)
  │     ├── Categories (/admin/categories)
  │     ├── Submissions (/admin/submissions)
  │     ├── Announcements (/admin/announcements)
  │     ├── Competition Settings (/admin/competition)
  │     └── Live Stats (/admin/competition/stats)
  ├── Security Operations
  │     ├── SOC Center (/admin/soc)
  │     ├── Threat Hunts (/admin/hunts)
  │     ├── Threat Intelligence (/admin/threat-intel)
  │     └── Incident Log (/admin/cyberrange/incidents)
  ├── Governance, Risk, Compliance
  │     ├── Compliance Monitor (/admin/compliance)
  │     ├── Risk Quantification (/admin/risk-quantification)
  │     ├── Resilience Center (/admin/resilience)
  │     └── Vendor Risk Register (/admin/resilience/vendors)
  └── Platform Settings
        ├── Mission Control (/admin/mission-control)
        ├── Organization (/admin/organization)
        ├── Plugins (/admin/plugins)
        ├── Users (/admin/users)
        └── AI Services (/admin/ai)
```

---

## 2. Screen Inventory & Consistency Report
- **Total Registered Screens**: 35 core administration and participant routes.
- **De-duplication Action**: Confirmed no orphaned layouts or duplicate views exist.
- **Navigation Consistency**: Sidebar panel triggers map cleanly to rail categories with automatic active link highlights matching `window.location.pathname`.
- **Keyboard navigation**: Unified palette triggers and shortcut listeners registered globally.
