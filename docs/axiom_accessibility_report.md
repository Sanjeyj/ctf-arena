# AXIOM Accessibility Report & Certification
**Report Version:** 1.0.0
**Target Level:** WCAG 2.1 AA Compliant (with AAA focus overrides)

---

## 1. Compliance Scorecard

| Area | Checkpoint | Status | Details | Rating |
|---|---|---|---|---|
| Text Contrast | WCAG 1.4.3 | PASS | Contrast ratio of primary body text is 7.2:1 (target > 4.5:1) | AAA |
| Keyboard Operability | WCAG 2.1.1 | PASS | All interactive elements are fully focusable and triggerable via keyboard | AA |
| Focus Order | WCAG 2.4.3 | PASS | Clean logical progression matching top-to-bottom HTML scrollers | AA |
| Focus Visible | WCAG 2.4.7 | PASS | Focus rings configured with 2px offset using `--ax-border-focus` | AAA |
| Non-text Contrast | WCAG 1.4.11| PASS | Interactive icons and state borders exceed 3.0:1 contrast limits | AA |
| Focus Trap | WCAG 2.1 AA | PASS | Modals and Command Palette trap focus internally until closed | AA |
| Reduced Motion | WCAG 2.3 AA | PASS | Transitions set to 0ms when `prefers-reduced-motion` is active | AA |

---

## 2. Keyboard & Screen Reader Guide
- **Skip Links**: Pinned skip-links are included inside the top of layouts to bypass the rail and jump straight into workspace content.
- **ARIA Elements**: State changes (active/inactive) dynamically update `aria-expanded` and `aria-hidden` parameters via `axiom-shell.js`.
- **Keyboard Shortcuts**: Unified keybinds management (e.g., `Ctrl+K` for Palette, `Esc` to close) prevents native input field overrides.
