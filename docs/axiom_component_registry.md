# AXIOM Component Registry
**Release Version:** 1.0.0

The following registry tracks the lifecycle, ownership, and quality ratings of all core components within the AXIOM design system.

---

## 1. Core Component Ledger

| ID | Name | Version | Owner | Accessibility | Performance | Keyboard | Status |
|---|---|---|---|---|---|---|---|
| `AX-001` | Buttons | 1.0.0 | Dev Team | AAA | 60 FPS | `Tab` / `Enter` | Frozen |
| `AX-002` | Cards | 1.0.0 | Dev Team | AA | 60 FPS | N/A | Frozen |
| `AX-003` | Tables | 1.0.0 | Dev Team | AA | 60 FPS | `Tab` / Arrows | Frozen |
| `AX-004` | Timeline | 1.0.0 | SOC Lead | AA | 60 FPS | Arrows | Active |
| `AX-005` | Logs Console | 1.0.0 | SOC Lead | AA | 58 FPS | N/A | Active |
| `AX-006` | Terminal | 1.0.0 | SOC Lead | AA | 60 FPS | Focus / Esc | Active |
| `AX-007` | Command Palette | 1.0.0 | Architect | AAA | 60 FPS | Full Bind | Frozen |
| `AX-008` | Dialog Modals | 1.0.0 | Dev Team | AAA | 60 FPS | Focus Trap | Frozen |
| `AX-009` | Drawers / Sheets | 1.0.0 | Dev Team | AA | 60 FPS | Esc Dismiss | Frozen |
| `AX-010` | Dropdowns | 1.0.0 | Dev Team | AA | 60 FPS | Arrows / Esc | Active |
| `AX-011` | Status Dot | 1.0.0 | Dev Team | AAA | 60 FPS | N/A | Frozen |
| `AX-012` | Skeleton Loaders | 1.0.0 | Dev Team | AAA | 60 FPS | N/A | Frozen |

---

## 2. Component Lifecycle Rules
- **Active:** In production and actively supported. No styling updates unless requested by accessibility/performance audits.
- **Deprecated:** Slated for replacement in subsequent major versions. Marked with a deprecation warning comment.
- **Frozen:** Fully locked. Part of the AXIOM core.
