# AXIOM Responsive & Viewport Guide
**Release Version:** 1.0.0

The AXIOM design system leverages a single responsive layout matrix to scale seamlessly from mobile screens to 5K and Ultrawide displays without code duplication.

---

## 1. Breakpoint System

| Viewport Category | Screen Width | Grid Layout behavior |
|---|---|---|
| Ultrawide / 4K / 5K | `>= 1920px` | Cards fixed at max-width limits, margins scale |
| Standard Desktop | `1200px - 1919px` | 12-column grid active, sidebar pinned (220px) |
| Laptop / Tablet Landscape | `768px - 1199px` | Columns collapse (`col-6` / `col-12`), sidebar pins |
| Mobile / Portrait | `< 768px` | Command Rail collapses, Hamburger drawer slides |

---

## 2. Layout Density Rules
- **Fluid containers**: Width margins scale dynamically using `--ax-space-scale` variables.
- **Large Displays**: Content areas enforce a centered `max-width: 1440px` to keep readable column widths and prevent visual fatigue on 4K/5K viewports.
