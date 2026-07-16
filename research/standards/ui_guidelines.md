# UI Design Guidelines & Style System — CDP v2.0

## 1. Design Philosophy

The user interface implements a dark futuristic theme using frosted glass surfaces, high-contrast text, and responsive grids:

- **Style Tokens**: Enforce CSS variables in `static/css/ui-modernization.css` for styling.
- **Glass surfaces**: Components use the `.ui-glass-card` class for container layouts.
- **Grids**: Dashboards use the `.ui-bento` grid system with column spans (`.ui-bento-4`, `.ui-bento-8`, `.ui-bento-12`).

---

## 2. Typography & Color Palette

- **Primary Font**: `Outfit` is used for headers and UI text.
- **Monospace Font**: `Fira Code` is used for numerical counts, hashes, IPs, and dates.
- **Accent Colors**:
  - Primary: `#00f0ff` (Cyan)
  - Secondary: `#8b5cf6` (Violet)
  - Success: `#10b981` (Green)
  - Danger: `#ef4444` (Red)
