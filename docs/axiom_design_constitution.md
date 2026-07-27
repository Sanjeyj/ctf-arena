# AXIOM Design Constitution
**Version:** 1.0.0
**Owner:** Design System Architecture Board

---

## 1. Naming Conventions

### 1.1 CSS Class Prefixes
- All utility classes, component wrappers, and tokens must use the `ax-` namespace.
- No legacy `ui-` classes may be added to any template files.
- Modifiers must use logical suffix naming:
  - Sizes: `.ax-btn-sm`, `.ax-btn-lg`
  - Colors/Semantics: `.ax-badge-green`, `.ax-badge-red`, `.ax-badge-blue`

### 1.2 Layout Systems
- The grid uses `.ax-grid` (parent) and `.ax-col-{n}` (children, where `1 <= n <= 12`).
- Content density should target a `4px` baseline spacing scale (`--ax-space-1` to `--ax-space-24`).

---

## 2. JavaScript Rules

- Custom interactions must be modularized and isolated to prevent global scope contamination.
- Scripts must hook onto unique selectors or data attributes (e.g., `id="ax-topbar"` or `data-ax-action`).
- Interactive triggers (dialogs, dropdowns, inspector drawers) must implement focus traps and `Escape` key handlers.

---

## 3. Accessibility & WCAG Compliance
- Contrast ratio between text and background must meet WCAG AA standards (minimum 4.5:1).
- Every interactive control must exhibit a focus ring with 2px offset using `--ax-border-focus`.
- Screen readers must be supported through semantic ARIA labels (`aria-expanded`, `aria-controls`, `aria-hidden`).
- Reduced motion preferences must disable animations instantly.

---

## 4. Performance Budgets
- Combined stylesheet bundle weight must remain below 100 KB.
- DOM depth must be kept under 32 nested levels to prevent browser reflow delays.
- Animations must be GPU-accelerated utilizing only `transform` and `opacity` properties.
