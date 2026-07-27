# AXIOM Visual Language & Interaction Guide
**Release Version:** 1.0.0

---

## 1. Visual Hierarchy Guidelines

- **Primary Heading (`32px`)**: Light font weight (`300`) with precise text color matching.
- **Data Columns & Numbers**: monospaced JetBrains Mono with elevated font weight.
- **Labels & Descriptions**: DIM/muted text to represent secondary contextual details.

---

## 2. Meaning of Colors
- **Blue**: Actionable links, secondary navigation triggers, information callouts.
- **Green**: Completed tasks, verified solutions, operational success.
- **Amber**: Warnings, configuration modifications required, low priority alerts.
- **Red**: Failed tasks, critical alerts, validation regressions detected.
- **Purple**: Autonomous AI capabilities, threat forecasting intelligence.
- **Zinc**: Inactive tabs, disabled states, placeholders.

---

## 3. Micro-Interactions & Hover Speeds
- All element hover animations must trigger within `100ms` (using `--ax-dur-micro` and `--ax-ease-out`) to prevent visual lag.
- Tooltips, inspector drawers, and detail panels slide out within `180ms` (`--ax-dur-context`) utilizing hardware-accelerated transforms.
