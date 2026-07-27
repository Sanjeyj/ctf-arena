# AXIOM Design Token Reference
**Release Version:** 1.0.0

All design tokens are defined as CSS Custom Properties in the root scope and are frozen as of Version 1.0.0.

---

## 1. Color Scale Tokens

### Surface & Backgrounds:
- `--ax-bg-base`: `#070910` (Viewport dark void)
- `--ax-bg-surface`: `#0D1018` (Primary shell header & rail)
- `--ax-bg-elevated`: `#111622` (Standard cards and workspace widgets)
- `--ax-bg-component`: `#16202E` (Input blocks, button surface)
- `--ax-bg-hover`: `#1C2A3A` (Component hover transitions)
- `--ax-bg-active`: `#223244` (Selected states)

### Status & Accents (WCAG Compliant):
- **Blue (Info/Interactive)**: `--ax-blue` (`#3B7DD8`), `--ax-blue-bright` (`#5B9BE8`)
- **Green (Success/Passed)**: `--ax-green` (`#2A9D6F`), `--ax-green-bright` (`#38C48C`)
- **Amber (Warning/Degraded)**: `--ax-amber` (`#C8890A`), `--ax-amber-bright` (`#E8A020`)
- **Red (Critical/Error)**: `--ax-red` (`#C43232`), `--ax-red-bright` (`#E04444`)
- **Purple (AI/Analytics)**: `--ax-purple` (`#7852CC`), `--ax-purple-bright` (`#9470E8`)

---

## 2. Typography Tokens
- **Sans font**: `'Inter', system-ui, sans-serif`
- **Mono font**: `'JetBrains Mono', monospace`
- **Scale**:
  - `--ax-text-2xs` (10px) · `--ax-text-xs` (11px) · `--ax-text-sm` (12px)
  - `--ax-text-base` (13px) · `--ax-text-md` (14px) · `--ax-text-lg` (16px)
  - `--ax-text-xl` (20px) · `--ax-text-2xl` (24px) · `--ax-text-3xl` (32px)

---

## 3. Spacing Scale (4px Grid)
- `--ax-space-1`: `4px`
- `--ax-space-2`: `8px`
- `--ax-space-3`: `12px`
- `--ax-space-4`: `16px`
- `--ax-space-5`: `20px`
- `--ax-space-6`: `24px`
- `--ax-space-8`: `32px`
- `--ax-space-12`: `48px`
- `--ax-space-14`: `56px`

---

## 4. Spacing, Radius, and Motion
- **Radius**: `--ax-radius-sm` (3px) · `--ax-radius-md` (6px) · `--ax-radius-lg` (8px) · `--ax-radius-xl` (12px)
- **Transitions**:
  - `--ax-ease-out`: `cubic-bezier(0, 0, 0.2, 1)` (Entering items)
  - `--ax-ease-spring`: `cubic-bezier(0.34, 1.56, 0.64, 1)` (Modals, quick-triggers)
  - Durations: micro (`100ms`), base (`200ms`), context (`180ms`), slow (`350ms`)
