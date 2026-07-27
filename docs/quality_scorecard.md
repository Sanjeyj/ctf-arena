# AXIOM Quality Scorecard
**Release Version:** 1.0.0

---

## 1. Quality Standards Checklist

| Area | Quality Parameter | Baseline Target | Measured Score | Status |
|---|---|---|---|---|
| Consistency | Naming, layouts, spacing, margins | 100% | 100% | PASS |
| Reuse | Reuses buttons, cards, tables, inputs | 100% | 100% | PASS |
| Compliance | Uses AXIOM tokens exclusively | 100% | 100% | PASS |
| Accessibility | WCAG AA compliance, focus visible | PASS | PASS | PASS |
| Performance | Lightweight CSS/JS footprint | < 150 KB | 110.8 KB | PASS |
| Regression | 100% pytest and DOM cert passes | 236/236 | 236/236 | PASS |

---

## 2. Template Audit Log
- **33 Templates Audited & Migrated**: All instances of `ui-` class names converted to `ax-` equivalents.
- **Visual Regression Baseline**: Reference screenshots generated for Dashboard, Scoreboard, Login, SOC, and Hunts.
